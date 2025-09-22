"""
RBAC Operations
Database operations for Role-Based Access Control and permissions
"""

from ..manager import DatabaseManager
from ..models import Context, ContextPermission, Organization, Team, User


class RBACOperations(DatabaseManager):
    """Role-Based Access Control database operations"""

    def share_context_with_user(
        self, context_id: int, user_id: int, permission_level: str, granted_by: int
    ):
        """Share a context with a specific user"""
        session = self.get_session()
        try:
            permission = ContextPermission(
                context_id=context_id,
                user_id=user_id,
                permission_level=permission_level,
                granted_by=granted_by,
            )
            session.add(permission)
            session.commit()
            return permission
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def share_context_with_team(
        self, context_id: int, team_id: int, permission_level: str, granted_by: int
    ):
        """Share a context with a team"""
        session = self.get_session()
        try:
            permission = ContextPermission(
                context_id=context_id,
                team_id=team_id,
                permission_level=permission_level,
                granted_by=granted_by,
            )
            session.add(permission)
            session.commit()
            return permission
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def share_context_with_organization(
        self,
        context_id: int,
        organization_id: int,
        permission_level: str,
        granted_by: int,
    ):
        """Share a context with an organization"""
        session = self.get_session()
        try:
            permission = ContextPermission(
                context_id=context_id,
                organization_id=organization_id,
                permission_level=permission_level,
                granted_by=granted_by,
            )
            session.add(permission)
            session.commit()
            return permission
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def check_context_permission(
        self, context_id: int, user_id: int, required_permission: str = "read"
    ):
        """Check if a user has permission to access a context"""
        session = self.get_session()
        try:
            # Check if user owns the context
            context = session.query(Context).filter(Context.id == context_id).first()
            if context and context.owner_id == user_id:
                return True  # Owner has all permissions

            # Permission hierarchy: admin > write > read
            permission_levels = {"read": 1, "write": 2, "admin": 3}
            required_level = permission_levels.get(required_permission, 1)

            # Check direct user permissions
            user_permission = (
                session.query(ContextPermission)
                .filter(
                    ContextPermission.context_id == context_id,
                    ContextPermission.user_id == user_id,
                )
                .first()
            )

            if user_permission:
                user_level = permission_levels.get(user_permission.permission_level, 0)
                if user_level >= required_level:
                    return True

            # Check team permissions
            from ..models import TeamMember

            team_permissions = (
                session.query(ContextPermission)
                .join(TeamMember, ContextPermission.team_id == TeamMember.team_id)
                .filter(
                    ContextPermission.context_id == context_id,
                    TeamMember.user_id == user_id,
                )
                .all()
            )

            for permission in team_permissions:
                team_level = permission_levels.get(permission.permission_level, 0)
                if team_level >= required_level:
                    return True

            # Check organization permissions
            org_permissions = (
                session.query(ContextPermission)
                .join(Team, ContextPermission.organization_id == Team.organization_id)
                .join(TeamMember, Team.id == TeamMember.team_id)
                .filter(
                    ContextPermission.context_id == context_id,
                    TeamMember.user_id == user_id,
                )
                .all()
            )

            for permission in org_permissions:
                org_level = permission_levels.get(permission.permission_level, 0)
                if org_level >= required_level:
                    return True

            return False
        except Exception as e:
            raise e
        finally:
            session.close()

    def get_user_contexts(self, user_id: int):
        """Get all contexts a user can access"""
        session = self.get_session()
        try:
            # Get owned contexts
            owned_contexts = (
                session.query(Context).filter(Context.owner_id == user_id).all()
            )

            # Get directly shared contexts
            shared_contexts = (
                session.query(Context)
                .join(ContextPermission)
                .filter(ContextPermission.user_id == user_id)
                .all()
            )

            # Get team-shared contexts
            from ..models import TeamMember

            team_contexts = (
                session.query(Context)
                .join(ContextPermission, Context.id == ContextPermission.context_id)
                .join(TeamMember, ContextPermission.team_id == TeamMember.team_id)
                .filter(TeamMember.user_id == user_id)
                .all()
            )

            # Get organization-shared contexts
            org_contexts = (
                session.query(Context)
                .join(ContextPermission, Context.id == ContextPermission.context_id)
                .join(Team, ContextPermission.organization_id == Team.organization_id)
                .join(TeamMember, Team.id == TeamMember.team_id)
                .filter(TeamMember.user_id == user_id)
                .all()
            )

            # Combine and deduplicate
            all_contexts = set()
            for context_list in [
                owned_contexts,
                shared_contexts,
                team_contexts,
                org_contexts,
            ]:
                all_contexts.update(context_list)

            return [
                {
                    "id": ctx.id,
                    "name": ctx.name,
                    "description": ctx.description,
                    "scope": ctx.scope,
                    "is_active": ctx.is_active,
                    "owner_id": ctx.owner_id,
                    "is_owner": ctx.owner_id == user_id,
                    "permission_level": self._get_user_context_permission_level(
                        ctx.id, user_id, session
                    ),
                }
                for ctx in all_contexts
            ]
        except Exception as e:
            raise e
        finally:
            session.close()

    def _get_user_context_permission_level(
        self, context_id: int, user_id: int, session
    ):
        """Get the highest permission level a user has for a context"""
        # Check if user owns the context
        context = session.query(Context).filter(Context.id == context_id).first()
        if context and context.owner_id == user_id:
            return "owner"

        permission_levels = {"read": 1, "write": 2, "admin": 3}
        max_level = 0
        max_permission = "none"

        # Check direct permissions
        user_permission = (
            session.query(ContextPermission)
            .filter(
                ContextPermission.context_id == context_id,
                ContextPermission.user_id == user_id,
            )
            .first()
        )

        if user_permission:
            level = permission_levels.get(user_permission.permission_level, 0)
            if level > max_level:
                max_level = level
                max_permission = user_permission.permission_level

        # Check team permissions
        from ..models import TeamMember

        team_permissions = (
            session.query(ContextPermission)
            .join(TeamMember, ContextPermission.team_id == TeamMember.team_id)
            .filter(
                ContextPermission.context_id == context_id,
                TeamMember.user_id == user_id,
            )
            .all()
        )

        for permission in team_permissions:
            level = permission_levels.get(permission.permission_level, 0)
            if level > max_level:
                max_level = level
                max_permission = permission.permission_level

        # Check organization permissions
        org_permissions = (
            session.query(ContextPermission)
            .join(Team, ContextPermission.organization_id == Team.organization_id)
            .join(TeamMember, Team.id == TeamMember.team_id)
            .filter(
                ContextPermission.context_id == context_id,
                TeamMember.user_id == user_id,
            )
            .all()
        )

        for permission in org_permissions:
            level = permission_levels.get(permission.permission_level, 0)
            if level > max_level:
                max_level = level
                max_permission = permission.permission_level

        return max_permission

    def revoke_context_permission(
        self, context_id: int, permission_id: int, user_id: int
    ):
        """Revoke a specific context permission"""
        session = self.get_session()
        try:
            # Check if user has permission to revoke (owner or admin)
            if not self.check_context_permission(context_id, user_id, "admin"):
                raise ValueError("Insufficient permissions to revoke access")

            permission = (
                session.query(ContextPermission)
                .filter(ContextPermission.id == permission_id)
                .first()
            )

            if not permission or permission.context_id != context_id:
                raise ValueError("Permission not found")

            session.delete(permission)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_context_permissions(self, context_id: int, user_id: int):
        """Get all permissions for a context (if user has admin access)"""
        session = self.get_session()
        try:
            # Check if user has admin permission
            if not self.check_context_permission(context_id, user_id, "admin"):
                raise ValueError("Insufficient permissions to view context permissions")

            permissions = (
                session.query(ContextPermission)
                .filter(ContextPermission.context_id == context_id)
                .all()
            )

            result = []
            for perm in permissions:
                perm_data = {
                    "id": perm.id,
                    "permission_level": perm.permission_level,
                    "granted_by": perm.granted_by,
                    "created_at": (
                        perm.created_at.isoformat() if perm.created_at else None
                    ),
                }

                if perm.user_id:
                    user = session.query(User).filter(User.id == perm.user_id).first()
                    perm_data["type"] = "user"
                    perm_data["target"] = (
                        {
                            "id": user.id,
                            "username": user.username,
                            "email": user.email,
                        }
                        if user
                        else None
                    )

                elif perm.team_id:
                    team = session.query(Team).filter(Team.id == perm.team_id).first()
                    perm_data["type"] = "team"
                    perm_data["target"] = (
                        {
                            "id": team.id,
                            "name": team.name,
                        }
                        if team
                        else None
                    )

                elif perm.organization_id:
                    org = (
                        session.query(Organization)
                        .filter(Organization.id == perm.organization_id)
                        .first()
                    )
                    perm_data["type"] = "organization"
                    perm_data["target"] = (
                        {
                            "id": org.id,
                            "name": org.name,
                        }
                        if org
                        else None
                    )

                result.append(perm_data)

            return result
        except Exception as e:
            raise e
        finally:
            session.close()

    def update_context_permission(
        self, permission_id: int, new_permission_level: str, user_id: int
    ):
        """Update an existing context permission"""
        session = self.get_session()
        try:
            permission = (
                session.query(ContextPermission)
                .filter(ContextPermission.id == permission_id)
                .first()
            )

            if not permission:
                raise ValueError("Permission not found")

            # Check if user has admin permission for the context
            if not self.check_context_permission(
                permission.context_id, user_id, "admin"
            ):
                raise ValueError(
                    "Insufficient permissions to modify context permissions"
                )

            permission.permission_level = new_permission_level
            session.commit()
            return permission
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def check_user_admin(self, user_id: int):
        """Check if user is a system administrator"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            return user and user.is_admin
        finally:
            session.close()

    def get_user_permissions_summary(self, user_id: int):
        """Get a summary of all permissions for a user"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return None

            # Count owned contexts
            owned_contexts = (
                session.query(Context).filter(Context.owner_id == user_id).count()
            )

            # Count direct permissions
            direct_permissions = (
                session.query(ContextPermission)
                .filter(ContextPermission.user_id == user_id)
                .count()
            )

            # Count team memberships
            from ..models import TeamMember

            team_memberships = (
                session.query(TeamMember).filter(TeamMember.user_id == user_id).count()
            )

            return {
                "user_id": user_id,
                "username": user.username,
                "is_admin": user.is_admin,
                "owned_contexts": owned_contexts,
                "direct_permissions": direct_permissions,
                "team_memberships": team_memberships,
            }
        finally:
            session.close()
