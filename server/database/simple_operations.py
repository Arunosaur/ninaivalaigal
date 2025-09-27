"""
Simple Database Operations - Temporary bypass for inheritance issues
Contains only the essential methods needed for auth to work
"""

from .manager import DatabaseManager
from .models import User

class SimpleDatabaseOperations(DatabaseManager):
    """Simplified database operations class without problematic inheritance"""
    
    def get_user_by_email(self, email: str):
        """Get user by email"""
        session = self.get_session()
        try:
            return session.query(User).filter(User.email == email).first()
        finally:
            session.close()
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        session = self.get_session()
        try:
            return session.query(User).filter(User.id == user_id).first()
        finally:
            session.close()
    
    def create_user(self, **kwargs):
        """Create a new user"""
        session = self.get_session()
        try:
            user = User(**kwargs)
            session.add(user)
            session.commit()
            return user
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def authenticate_user(self, email: str, password_hash: str):
        """Authenticate user by email and password hash"""
        user = self.get_user_by_email(email)
        if user and user.password_hash == password_hash:
            return user
        return None
