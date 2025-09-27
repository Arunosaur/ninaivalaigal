"""
SPEC-007: Unified Context Scope System Operations
Complete implementation of context management with personal/team/organization scopes
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Union

import asyncpg

logger = logging.getLogger(__name__)

# Type definitions for SPEC-007
ContextScope = Literal["personal", "team", "organization"]
ContextVisibility = Literal["private", "shared", "public"]
PermissionLevel = Literal["read", "write", "admin", "owner"]


class UnifiedContextOps:
    """
    SPEC-007: Unified Context Scope System Operations
    Implements complete context management with scopes, permissions, and sharing
    """

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def create_context(
        self,
        name: str,
        description: Optional[str] = None,
        scope: ContextScope = "personal",
        owner_id: Optional[int] = None,
        team_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        visibility: ContextVisibility = "private",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new context with proper scope validation"""

        # Validate scope ownership
        if scope == "personal" and not owner_id:
            raise ValueError("Personal contexts require owner_id")
        elif scope == "team" and not team_id:
            raise ValueError("Team contexts require team_id")
        elif scope == "organization" and not organization_id:
            raise ValueError("Organization contexts require organization_id")

        async with self.pool.acquire() as conn:
            # Check for duplicate context names within scope
            existing = await self._check_context_exists(
                conn, name, scope, owner_id, team_id, organization_id
            )
            if existing:
                raise ValueError(f"Context '{name}' already exists in {scope} scope")

            # Insert new context
            query = """
                INSERT INTO contexts (
                    name, description, scope, owner_id, team_id, organization_id,
                    visibility, metadata, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $9)
                RETURNING id, name, scope, visibility, created_at
            """

            now = datetime.now(timezone.utc)
            metadata_json = json.dumps(metadata or {})

            result = await conn.fetchrow(
                query,
                name,
                description,
                scope,
                owner_id,
                team_id,
                organization_id,
                visibility,
                metadata_json,
                now,
            )

            # Create owner permission for personal contexts
            if scope == "personal" and owner_id:
                await self._grant_permission(
                    conn,
                    result["id"],
                    user_id=owner_id,
                    permission_level="owner",
                    granted_by=owner_id,
                )

            logger.info(f"Created {scope} context '{name}' with ID {result['id']}")
            return dict(result)

    async def get_context(
        self, context_id: int, user_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Get context by ID with access validation"""
        async with self.pool.acquire() as conn:
            # Check user access to context
            if user_id and not await self._check_context_access(
                conn, context_id, user_id
            ):
                return None

            query = """
                SELECT c.*,
                       COALESCE(ca.permission_level, 'none') as user_permission
                FROM contexts c
                LEFT JOIN context_access ca ON c.id = ca.context_id AND ca.user_id = $2
                WHERE c.id = $1 AND c.is_active = true
            """

            result = await conn.fetchrow(query, context_id, user_id)
            return dict(result) if result else None

    async def list_contexts(
        self,
        user_id: Optional[int] = None,
        scope: Optional[ContextScope] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List contexts accessible to user with optional scope filtering"""
        async with self.pool.acquire() as conn:
            conditions = ["c.is_active = true"]
            params = []
            param_count = 0

            if user_id:
                param_count += 1
                conditions.append(f"ca.user_id = ${param_count}")
                params.append(user_id)

            if scope:
                param_count += 1
                conditions.append(f"c.scope = ${param_count}")
                params.append(scope)

            param_count += 1
            params.append(limit)
            limit_param = f"${param_count}"

            param_count += 1
            params.append(offset)
            offset_param = f"${param_count}"

            query = f"""
                SELECT DISTINCT c.id, c.name, c.description, c.scope, c.visibility,
                       c.created_at, c.updated_at, ca.permission_level
                FROM contexts c
                LEFT JOIN context_access ca ON c.id = ca.context_id
                WHERE {' AND '.join(conditions)}
                ORDER BY c.updated_at DESC
                LIMIT {limit_param} OFFSET {offset_param}
            """

            results = await conn.fetch(query, *params)
            return [dict(row) for row in results]

    async def update_context(
        self,
        context_id: int,
        user_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        visibility: Optional[ContextVisibility] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update context with permission validation"""
        async with self.pool.acquire() as conn:
            # Check write permission
            if not await self._check_context_access(
                conn, context_id, user_id, min_level="write"
            ):
                raise PermissionError("Insufficient permissions to update context")

            updates = []
            params = [context_id]
            param_count = 1

            if name is not None:
                param_count += 1
                updates.append(f"name = ${param_count}")
                params.append(name)

            if description is not None:
                param_count += 1
                updates.append(f"description = ${param_count}")
                params.append(description)

            if visibility is not None:
                param_count += 1
                updates.append(f"visibility = ${param_count}")
                params.append(visibility)

            if metadata is not None:
                param_count += 1
                updates.append(f"metadata = ${param_count}")
                params.append(json.dumps(metadata))

            if not updates:
                return True

            param_count += 1
            updates.append(f"updated_at = ${param_count}")
            params.append(datetime.now(timezone.utc))

            query = f"""
                UPDATE contexts
                SET {', '.join(updates)}
                WHERE id = $1 AND is_active = true
            """

            result = await conn.execute(query, *params)
            success = result.split()[-1] == "1"  # Check if one row was updated

            if success:
                logger.info(f"Updated context {context_id} by user {user_id}")

            return success

    async def delete_context(self, context_id: int, user_id: int) -> bool:
        """Soft delete context with permission validation"""
        async with self.pool.acquire() as conn:
            # Check admin/owner permission
            if not await self._check_context_access(
                conn, context_id, user_id, min_level="admin"
            ):
                raise PermissionError("Insufficient permissions to delete context")

            query = """
                UPDATE contexts
                SET is_active = false, updated_at = $2
                WHERE id = $1 AND is_active = true
            """

            result = await conn.execute(query, context_id, datetime.now(timezone.utc))
            success = result.split()[-1] == "1"

            if success:
                logger.info(f"Deleted context {context_id} by user {user_id}")

            return success

    async def grant_permission(
        self,
        context_id: int,
        granted_by: int,
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        permission_level: PermissionLevel = "read",
        expires_at: Optional[datetime] = None,
    ) -> bool:
        """Grant permission to user, team, or organization"""
        async with self.pool.acquire() as conn:
            # Check granter has admin permission
            if not await self._check_context_access(
                conn, context_id, granted_by, min_level="admin"
            ):
                raise PermissionError("Insufficient permissions to grant access")

            return await self._grant_permission(
                conn,
                context_id,
                user_id,
                team_id,
                organization_id,
                permission_level,
                granted_by,
                expires_at,
            )

    async def revoke_permission(
        self,
        context_id: int,
        revoked_by: int,
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
        organization_id: Optional[int] = None,
    ) -> bool:
        """Revoke permission from user, team, or organization"""
        async with self.pool.acquire() as conn:
            # Check revoker has admin permission
            if not await self._check_context_access(
                conn, context_id, revoked_by, min_level="admin"
            ):
                raise PermissionError("Insufficient permissions to revoke access")

            conditions = ["context_id = $1"]
            params = [context_id]
            param_count = 1

            if user_id:
                param_count += 1
                conditions.append(f"user_id = ${param_count}")
                params.append(user_id)
            elif team_id:
                param_count += 1
                conditions.append(f"team_id = ${param_count}")
                params.append(team_id)
            elif organization_id:
                param_count += 1
                conditions.append(f"organization_id = ${param_count}")
                params.append(organization_id)
            else:
                raise ValueError("Must specify user_id, team_id, or organization_id")

            query = f"""
                DELETE FROM context_permissions
                WHERE {' AND '.join(conditions)}
            """

            result = await conn.execute(query, *params)
            success = int(result.split()[-1]) > 0

            if success:
                logger.info(
                    f"Revoked permission on context {context_id} by user {revoked_by}"
                )

            return success

    async def share_context(
        self,
        context_id: int,
        shared_by: int,
        shared_with_user_id: Optional[int] = None,
        shared_with_team_id: Optional[int] = None,
        shared_with_organization_id: Optional[int] = None,
        permission_level: Literal["read", "write"] = "read",
        message: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> bool:
        """Share context with user, team, or organization"""
        async with self.pool.acquire() as conn:
            # Check sharer has write permission
            if not await self._check_context_access(
                conn, context_id, shared_by, min_level="write"
            ):
                raise PermissionError("Insufficient permissions to share context")

            query = """
                INSERT INTO context_shares (
                    context_id, shared_with_user_id, shared_with_team_id,
                    shared_with_organization_id, shared_by, permission_level,
                    message, expires_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (context_id, shared_with_user_id, shared_with_team_id, shared_with_organization_id)
                DO UPDATE SET
                    permission_level = EXCLUDED.permission_level,
                    message = EXCLUDED.message,
                    expires_at = EXCLUDED.expires_at,
                    created_at = CURRENT_TIMESTAMP
            """

            await conn.execute(
                query,
                context_id,
                shared_with_user_id,
                shared_with_team_id,
                shared_with_organization_id,
                shared_by,
                permission_level,
                message,
                expires_at,
            )

            logger.info(f"Shared context {context_id} by user {shared_by}")
            return True

    # Private helper methods
    async def _check_context_exists(
        self,
        conn: asyncpg.Connection,
        name: str,
        scope: ContextScope,
        owner_id: Optional[int] = None,
        team_id: Optional[int] = None,
        organization_id: Optional[int] = None,
    ) -> bool:
        """Check if context with same name exists in scope"""
        query = """
            SELECT 1 FROM contexts
            WHERE name = $1 AND scope = $2 AND is_active = true
            AND (
                (scope = 'personal' AND owner_id = $3) OR
                (scope = 'team' AND team_id = $4) OR
                (scope = 'organization' AND organization_id = $5)
            )
        """

        result = await conn.fetchval(
            query, name, scope, owner_id, team_id, organization_id
        )
        return result is not None

    async def _check_context_access(
        self,
        conn: asyncpg.Connection,
        context_id: int,
        user_id: int,
        min_level: PermissionLevel = "read",
    ) -> bool:
        """Check if user has minimum permission level for context"""
        query = """
            SELECT permission_level FROM context_access
            WHERE context_id = $1 AND user_id = $2
        """

        permission = await conn.fetchval(query, context_id, user_id)
        if not permission:
            return False

        # Permission hierarchy: read < write < admin < owner
        levels = {"read": 1, "write": 2, "admin": 3, "owner": 4}
        return levels.get(permission, 0) >= levels.get(min_level, 0)

    async def _grant_permission(
        self,
        conn: asyncpg.Connection,
        context_id: int,
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        permission_level: PermissionLevel = "read",
        granted_by: Optional[int] = None,
        expires_at: Optional[datetime] = None,
    ) -> bool:
        """Internal method to grant permission"""
        query = """
            INSERT INTO context_permissions (
                context_id, user_id, team_id, organization_id,
                permission_level, granted_by, expires_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (context_id, user_id, team_id, organization_id)
            DO UPDATE SET
                permission_level = EXCLUDED.permission_level,
                granted_by = EXCLUDED.granted_by,
                expires_at = EXCLUDED.expires_at,
                granted_at = CURRENT_TIMESTAMP
        """

        await conn.execute(
            query,
            context_id,
            user_id,
            team_id,
            organization_id,
            permission_level,
            granted_by,
            expires_at,
        )

        return True

    async def get_context_permissions(
        self, context_id: int, user_id: int
    ) -> List[Dict[str, Any]]:
        """Get all permissions for a context (admin only)"""
        async with self.pool.acquire() as conn:
            if not await self._check_context_access(
                conn, context_id, user_id, min_level="admin"
            ):
                raise PermissionError(
                    "Insufficient permissions to view context permissions"
                )

            query = """
                SELECT cp.*, u.username, t.name as team_name, o.name as org_name
                FROM context_permissions cp
                LEFT JOIN users u ON cp.user_id = u.id
                LEFT JOIN teams t ON cp.team_id = t.id
                LEFT JOIN organizations o ON cp.organization_id = o.id
                WHERE cp.context_id = $1
                ORDER BY cp.granted_at DESC
            """

            results = await conn.fetch(query, context_id)
            return [dict(row) for row in results]

    async def health_check(self) -> bool:
        """Check if context operations are healthy"""
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Context operations health check failed: {e}")
            return False
