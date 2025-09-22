"""
Organization Operations
Database operations for organization and team management
"""

from ..manager import DatabaseManager
from ..models import Organization, Team, TeamMember


class OrganizationOperations(DatabaseManager):
    """Organization and team-related database operations"""

    # Organization Operations
    def create_organization(self, name: str, description: str = None):
        """Create a new organization"""
        session = self.get_session()
        try:
            organization = Organization(name=name, description=description)
            session.add(organization)
            session.commit()
            return organization
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_organization_by_name(self, name: str):
        """Get organization by name"""
        session = self.get_session()
        try:
            return session.query(Organization).filter(Organization.name == name).first()
        finally:
            session.close()

    def get_organization_by_id(self, organization_id: int):
        """Get organization by ID"""
        session = self.get_session()
        try:
            return (
                session.query(Organization)
                .filter(Organization.id == organization_id)
                .first()
            )
        finally:
            session.close()

    def get_all_organizations(self):
        """Get all organizations"""
        session = self.get_session()
        try:
            return session.query(Organization).all()
        finally:
            session.close()

    def update_organization(
        self, organization_id: int, name: str = None, description: str = None
    ):
        """Update organization information"""
        session = self.get_session()
        try:
            org = (
                session.query(Organization)
                .filter(Organization.id == organization_id)
                .first()
            )
            if not org:
                raise ValueError(f"Organization with ID {organization_id} not found")

            if name is not None:
                # Check for name conflicts
                existing = (
                    session.query(Organization)
                    .filter(
                        Organization.name == name, Organization.id != organization_id
                    )
                    .first()
                )
                if existing:
                    raise ValueError(f"Organization name '{name}' already exists")
                org.name = name

            if description is not None:
                org.description = description

            session.commit()
            return org
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_organization(self, organization_id: int):
        """Delete an organization"""
        session = self.get_session()
        try:
            org = (
                session.query(Organization)
                .filter(Organization.id == organization_id)
                .first()
            )
            if not org:
                raise ValueError(f"Organization with ID {organization_id} not found")

            # TODO: Handle cascading deletes for teams and members
            session.delete(org)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_organization_teams(self, organization_id: int):
        """Get all teams in an organization"""
        session = self.get_session()
        try:
            return (
                session.query(Team)
                .filter(Team.organization_id == organization_id)
                .all()
            )
        finally:
            session.close()

    def get_user_organizations(self, user_id: int):
        """Get all organizations a user belongs to (via teams)"""
        session = self.get_session()
        try:
            organizations = (
                session.query(Organization)
                .join(Team)
                .join(TeamMember)
                .filter(TeamMember.user_id == user_id)
                .distinct()
                .all()
            )
            return organizations
        except Exception as e:
            raise e
        finally:
            session.close()

    # Team Operations
    def create_team(
        self, name: str, organization_id: int = None, description: str = None
    ):
        """Create a new team"""
        session = self.get_session()
        try:
            team = Team(
                name=name, organization_id=organization_id, description=description
            )
            session.add(team)
            session.commit()
            return team
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_team_by_id(self, team_id: int):
        """Get team by ID"""
        session = self.get_session()
        try:
            return session.query(Team).filter(Team.id == team_id).first()
        finally:
            session.close()

    def get_team_by_name(self, name: str, organization_id: int = None):
        """Get team by name within an organization"""
        session = self.get_session()
        try:
            query = session.query(Team).filter(Team.name == name)
            if organization_id:
                query = query.filter(Team.organization_id == organization_id)
            return query.first()
        finally:
            session.close()

    def update_team(
        self,
        team_id: int,
        name: str = None,
        description: str = None,
        organization_id: int = None,
    ):
        """Update team information"""
        session = self.get_session()
        try:
            team = session.query(Team).filter(Team.id == team_id).first()
            if not team:
                raise ValueError(f"Team with ID {team_id} not found")

            if name is not None:
                team.name = name
            if description is not None:
                team.description = description
            if organization_id is not None:
                team.organization_id = organization_id

            session.commit()
            return team
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_team(self, team_id: int):
        """Delete a team"""
        session = self.get_session()
        try:
            team = session.query(Team).filter(Team.id == team_id).first()
            if not team:
                raise ValueError(f"Team with ID {team_id} not found")

            # TODO: Handle cascading deletes for team members
            session.delete(team)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def add_team_member(self, team_id: int, user_id: int, role: str = "member"):
        """Add a user to a team with a specific role"""
        session = self.get_session()
        try:
            # Check if membership already exists
            existing = (
                session.query(TeamMember)
                .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
                .first()
            )

            if existing:
                # Update role if membership exists
                existing.role = role
            else:
                # Create new membership
                member = TeamMember(team_id=team_id, user_id=user_id, role=role)
                session.add(member)

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def remove_team_member(self, team_id: int, user_id: int):
        """Remove a member from a team"""
        session = self.get_session()
        try:
            member = (
                session.query(TeamMember)
                .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
                .first()
            )

            if not member:
                raise ValueError("Team membership not found")

            session.delete(member)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_user_teams(self, user_id: int):
        """Get all teams a user belongs to"""
        session = self.get_session()
        try:
            teams = (
                session.query(Team)
                .join(TeamMember)
                .filter(TeamMember.user_id == user_id)
                .all()
            )
            return teams
        except Exception as e:
            raise e
        finally:
            session.close()

    def get_team_members(self, team_id: int):
        """Get all members of a team with their roles"""
        session = self.get_session()
        try:
            from ..models import User

            members = (
                session.query(TeamMember, User)
                .join(User)
                .filter(TeamMember.team_id == team_id)
                .all()
            )

            return [
                {
                    "user_id": member.user_id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": member.role,
                    "joined_at": (
                        member.created_at.isoformat() if member.created_at else None
                    ),
                }
                for member, user in members
            ]
        except Exception as e:
            raise e
        finally:
            session.close()

    def update_team_member_role(self, team_id: int, user_id: int, role: str):
        """Update a team member's role"""
        session = self.get_session()
        try:
            member = (
                session.query(TeamMember)
                .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
                .first()
            )

            if not member:
                raise ValueError("Team membership not found")

            member.role = role
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_team_stats(self, team_id: int):
        """Get team statistics"""
        session = self.get_session()
        try:
            team = session.query(Team).filter(Team.id == team_id).first()
            if not team:
                return None

            member_count = (
                session.query(TeamMember).filter(TeamMember.team_id == team_id).count()
            )

            # Count roles
            role_counts = {}
            roles = (
                session.query(TeamMember.role)
                .filter(TeamMember.team_id == team_id)
                .all()
            )
            for (role,) in roles:
                role_counts[role] = role_counts.get(role, 0) + 1

            return {
                "team_id": team_id,
                "name": team.name,
                "description": team.description,
                "organization_id": team.organization_id,
                "member_count": member_count,
                "role_distribution": role_counts,
                "created_at": team.created_at.isoformat() if team.created_at else None,
            }
        finally:
            session.close()

    def is_user_team_member(self, team_id: int, user_id: int):
        """Check if user is a member of a team"""
        session = self.get_session()
        try:
            member = (
                session.query(TeamMember)
                .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
                .first()
            )
            return member is not None
        finally:
            session.close()

    def get_user_team_role(self, team_id: int, user_id: int):
        """Get user's role in a specific team"""
        session = self.get_session()
        try:
            member = (
                session.query(TeamMember)
                .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
                .first()
            )
            return member.role if member else None
        finally:
            session.close()
