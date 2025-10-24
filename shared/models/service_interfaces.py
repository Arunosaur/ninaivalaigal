# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
Service Interface Definitions

Defines interfaces for inter-service communication after Task #88 (Core API Decomposition).
These interfaces prepare for the microservice architecture split.

Created as part of US #91: Core API Interface Refactoring Prep
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr

# ============================================================================
# Common Models
# ============================================================================


class AuthToken(BaseModel):
    """JWT authentication token"""

    access_token: str
    token_type: str
    expires_at: datetime
    user_id: str
    refresh_token: Optional[str] = None


class User(BaseModel):
    """User model"""

    id: str
    email: EmailStr
    name: str
    roles: List[str]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None


class Team(BaseModel):
    """Team model"""

    id: str
    name: str
    owner_id: str
    members: List[str]
    created_at: datetime
    is_active: bool


class Memory(BaseModel):
    """Memory model"""

    id: str
    user_id: str
    content: str
    context: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    embedding: Optional[List[float]] = None
    relevance_score: Optional[float] = None


class Invoice(BaseModel):
    """Invoice model"""

    id: str
    team_id: str
    amount: float
    currency: str
    status: str
    due_date: datetime
    created_at: datetime


# ============================================================================
# Service 1: Core API Interface (Authentication & User Management)
# ============================================================================


class CoreAPIInterface(ABC):
    """
    Interface for Core API Service

    Responsibilities:
    - User authentication and authorization
    - JWT token generation and validation
    - RBAC (Role-Based Access Control)
    - Session management

    Port: 13390
    """

    @abstractmethod
    async def authenticate(self, email: str, password: str) -> AuthToken:
        """
        Authenticate user and return JWT token

        Args:
            email: User email
            password: User password

        Returns:
            AuthToken with access/refresh tokens

        Raises:
            AuthenticationError: If credentials invalid
        """
        ...

    @abstractmethod
    async def validate_token(self, token: str) -> User:
        """
        Validate JWT token and return user

        Args:
            token: JWT access token

        Returns:
            User object if token valid

        Raises:
            TokenExpiredError: If token expired
            TokenInvalidError: If token invalid
        """
        ...

    @abstractmethod
    async def check_permission(self, user_id: str, resource: str, action: str) -> bool:
        """
        Check if user has permission for action on resource

        Args:
            user_id: User ID
            resource: Resource name (e.g., "team", "memory")
            action: Action name (e.g., "read", "write", "delete")

        Returns:
            True if user has permission, False otherwise
        """
        ...

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> AuthToken:
        """
        Refresh access token using refresh token

        Args:
            refresh_token: Refresh token

        Returns:
            New AuthToken
        """
        ...


# ============================================================================
# Service 2: Team Management Interface
# ============================================================================


class TeamServiceInterface(ABC):
    """
    Interface for Team Management Service

    Responsibilities:
    - Team creation and management
    - Organization hierarchy
    - Team memberships
    - Invitations

    Proposed Port: 13391
    """

    @abstractmethod
    async def create_team(self, name: str, owner_id: str, organization_id: Optional[str] = None) -> Team:
        """Create new team"""
        ...

    @abstractmethod
    async def get_user_teams(self, user_id: str) -> List[Team]:
        """Get all teams for user"""
        ...

    @abstractmethod
    async def add_team_member(self, team_id: str, user_id: str, role: str) -> bool:
        """Add member to team with specific role"""
        ...

    @abstractmethod
    async def check_team_membership(self, team_id: str, user_id: str) -> bool:
        """Check if user is member of team"""
        ...


# ============================================================================
# Service 3: Memory Service Interface (Rust)
# ============================================================================


class MemoryServiceInterface(ABC):
    """
    Interface for Memory Service (Rust implementation)

    Responsibilities:
    - Memory storage and retrieval
    - Memory embedding (pgvector)
    - Memory access control
    - Memory preloading and caching

    Current Port: 13393
    """

    @abstractmethod
    async def store_memory(
        self, user_id: str, content: str, context: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store memory and return memory ID

        Args:
            user_id: User ID
            content: Memory content
            context: Optional context
            metadata: Optional metadata

        Returns:
            Memory ID
        """
        ...

    @abstractmethod
    async def retrieve_memories(
        self, user_id: str, query: str, limit: int = 20, threshold: float = 0.7
    ) -> List[Memory]:
        """
        Retrieve relevant memories for user

        Args:
            user_id: User ID
            query: Search query
            limit: Maximum number of results
            threshold: Similarity threshold (0-1)

        Returns:
            List of matching memories with relevance scores
        """
        ...

    @abstractmethod
    async def delete_memory(self, memory_id: str, user_id: str) -> bool:
        """
        Delete memory

        Args:
            memory_id: Memory ID
            user_id: User ID (for authorization)

        Returns:
            True if deleted successfully
        """
        ...

    @abstractmethod
    async def preload_memories(self, user_id: str, strategy: str = "recent") -> int:
        """
        Preload memories into cache

        Args:
            user_id: User ID
            strategy: Preloading strategy ("recent", "frequent", "important")

        Returns:
            Number of memories preloaded
        """
        ...


# ============================================================================
# Service 4: Graph & AI Intelligence Interface (Rust/Go)
# ============================================================================


class GraphIntelligenceInterface(ABC):
    """
    Interface for Graph & AI Intelligence Service

    Responsibilities:
    - Apache AGE graph operations
    - AI-powered insights
    - Graph intelligence queries
    - Macro execution

    Current Port: 13398
    """

    @abstractmethod
    async def execute_cypher_query(
        self, user_id: str, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute Cypher query on graph database"""
        ...

    @abstractmethod
    async def get_insights(self, user_id: str, context: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get AI-powered insights for user"""
        ...

    @abstractmethod
    async def execute_macro(
        self, macro_id: str, user_id: str, parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute procedural macro"""
        ...


# ============================================================================
# Service 5: Business & Billing Interface
# ============================================================================


class BusinessServiceInterface(ABC):
    """
    Interface for Business & Billing Service

    Responsibilities:
    - Stripe payment processing
    - Invoice generation
    - Usage tracking and metering
    - Subscription management

    Proposed Port: 13392
    """

    @abstractmethod
    async def create_subscription(self, team_id: str, plan_id: str, payment_method_id: str) -> Dict[str, Any]:
        """Create new subscription"""
        ...

    @abstractmethod
    async def generate_invoice(self, team_id: str, period_start: datetime, period_end: datetime) -> Invoice:
        """Generate invoice for billing period"""
        ...

    @abstractmethod
    async def track_usage(self, team_id: str, metric: str, value: float, timestamp: Optional[datetime] = None) -> bool:
        """Track usage metric"""
        ...

    @abstractmethod
    async def get_usage_analytics(self, team_id: str, period_start: datetime, period_end: datetime) -> Dict[str, Any]:
        """Get usage analytics for period"""
        ...


# ============================================================================
# Service 6: Platform & Admin Interface
# ============================================================================


class PlatformAdminInterface(ABC):
    """
    Interface for Platform & Admin Service

    Responsibilities:
    - Multi-tenant administration
    - Platform-wide analytics
    - Performance monitoring
    - Partner integrations

    Proposed Port: 13394
    """

    @abstractmethod
    async def get_platform_metrics(self) -> Dict[str, Any]:
        """Get platform-wide metrics"""
        ...

    @abstractmethod
    async def manage_tenant(self, tenant_id: str, action: str) -> bool:
        """Manage tenant (activate, deactivate, etc.)"""
        ...


# ============================================================================
# Service 7: Social & Collaboration Interface
# ============================================================================


class SocialServiceInterface(ABC):
    """
    Interface for Social & Collaboration Service

    Responsibilities:
    - Discussions and comments
    - User feedback collection
    - Activity timeline
    - Suggestions engine

    Proposed Port: 13397
    """

    @abstractmethod
    async def create_discussion(self, user_id: str, title: str, content: str, team_id: Optional[str] = None) -> str:
        """Create new discussion"""
        ...

    @abstractmethod
    async def add_comment(self, discussion_id: str, user_id: str, content: str) -> str:
        """Add comment to discussion"""
        ...

    @abstractmethod
    async def get_timeline(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get activity timeline for user"""
        ...


# ============================================================================
# Usage Example
# ============================================================================

"""
# Example: Core API calling Memory Service

from shared.models.service_interfaces import MemoryServiceInterface, CoreAPIInterface

async def handle_memory_request(request):
    # Validate token via Core API
    core_api: CoreAPIInterface = get_core_api_client()
    user = await core_api.validate_token(request.headers['Authorization'])

    # Store memory via Memory Service
    memory_service: MemoryServiceInterface = get_memory_service_client()
    memory_id = await memory_service.store_memory(
        user_id=user.id,
        content=request.json['content'],
        context=request.json.get('context')
    )

    return {'memory_id': memory_id}
"""
