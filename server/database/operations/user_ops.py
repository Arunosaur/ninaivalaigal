"""
User Operations
Database operations for user management
"""

from ..manager import DatabaseManager
from ..models import User


class UserOperations(DatabaseManager):
    """User-related database operations"""

    def get_user_by_id(self, user_id: int):
        """Get user by ID"""
        session = self.get_session()
        try:
            return session.query(User).filter(User.id == user_id).first()
        finally:
            session.close()

    def get_user_by_email(self, email: str):
        """Get user by email"""
        session = self.get_session()
        try:
            return session.query(User).filter(User.email == email).first()
        finally:
            session.close()

    def get_user_by_username(self, username: str):
        """Get user by username"""
        session = self.get_session()
        try:
            return session.query(User).filter(User.username == username).first()
        finally:
            session.close()

    def create_user(
        self,
        username: str,
        email: str,
        password_hash: str = None,
        full_name: str = None,
        is_active: bool = True,
        is_admin: bool = False,
    ):
        """Create a new user"""
        session = self.get_session()
        try:
            # Check if user already exists
            existing_user = (
                session.query(User)
                .filter((User.username == username) | (User.email == email))
                .first()
            )

            if existing_user:
                if existing_user.username == username:
                    raise ValueError(f"Username '{username}' already exists")
                if existing_user.email == email:
                    raise ValueError(f"Email '{email}' already exists")

            user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                full_name=full_name,
                is_active=is_active,
                is_admin=is_admin,
            )

            session.add(user)
            session.commit()
            return user
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def update_user(
        self,
        user_id: int,
        username: str = None,
        email: str = None,
        password_hash: str = None,
        full_name: str = None,
        is_active: bool = None,
        is_admin: bool = None,
    ):
        """Update user information"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User with ID {user_id} not found")

            # Check for conflicts if updating username or email
            if username and username != user.username:
                existing = session.query(User).filter(User.username == username).first()
                if existing:
                    raise ValueError(f"Username '{username}' already exists")
                user.username = username

            if email and email != user.email:
                existing = session.query(User).filter(User.email == email).first()
                if existing:
                    raise ValueError(f"Email '{email}' already exists")
                user.email = email

            # Update other fields
            if password_hash is not None:
                user.password_hash = password_hash
            if full_name is not None:
                user.full_name = full_name
            if is_active is not None:
                user.is_active = is_active
            if is_admin is not None:
                user.is_admin = is_admin

            session.commit()
            return user
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_user(self, user_id: int):
        """Delete a user (soft delete by setting is_active=False)"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User with ID {user_id} not found")

            # Soft delete - set as inactive
            user.is_active = False
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def hard_delete_user(self, user_id: int):
        """Permanently delete a user and all associated data"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User with ID {user_id} not found")

            # TODO: Handle cascading deletes for related data
            # - User's contexts
            # - User's memories
            # - Team memberships
            # - Permissions

            session.delete(user)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_all_users(self, include_inactive: bool = False):
        """Get all users"""
        session = self.get_session()
        try:
            query = session.query(User)
            if not include_inactive:
                query = query.filter(User.is_active == True)

            return query.all()
        finally:
            session.close()

    def search_users(self, query: str, limit: int = 50):
        """Search users by username, email, or full name"""
        session = self.get_session()
        try:
            users = (
                session.query(User)
                .filter(
                    (User.username.ilike(f"%{query}%"))
                    | (User.email.ilike(f"%{query}%"))
                    | (User.full_name.ilike(f"%{query}%"))
                )
                .filter(User.is_active == True)
                .limit(limit)
                .all()
            )
            return users
        finally:
            session.close()

    def authenticate_user(self, username_or_email: str, password_hash: str):
        """Authenticate user by username/email and password hash"""
        session = self.get_session()
        try:
            user = (
                session.query(User)
                .filter(
                    (
                        (User.username == username_or_email)
                        | (User.email == username_or_email)
                    )
                    & (User.password_hash == password_hash)
                    & (User.is_active == True)
                )
                .first()
            )
            return user
        finally:
            session.close()

    def get_user_stats(self, user_id: int):
        """Get user statistics"""
        session = self.get_session()
        try:
            from ..models import Context, Memory

            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return None

            # Count user's contexts
            context_count = (
                session.query(Context).filter(Context.owner_id == user_id).count()
            )

            # Count user's memories
            memory_count = (
                session.query(Memory)
                .join(Context)
                .filter(Context.owner_id == user_id)
                .count()
            )

            return {
                "user_id": user_id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_admin": user.is_admin,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "context_count": context_count,
                "memory_count": memory_count,
            }
        finally:
            session.close()

    def update_last_login(self, user_id: int):
        """Update user's last login timestamp"""
        session = self.get_session()
        try:
            from datetime import datetime

            user = session.query(User).filter(User.id == user_id).first()
            if user:
                user.last_login = datetime.utcnow()
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def set_user_admin(self, user_id: int, is_admin: bool):
        """Set user admin status"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User with ID {user_id} not found")

            user.is_admin = is_admin
            session.commit()
            return user
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
