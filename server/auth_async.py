"""
Async-compatible authentication functions
Fixes the async/sync mismatch causing /auth/login to hang
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import bcrypt
import jwt
from database import User
from database.simple_operations import SimpleDatabaseOperations

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET = "your-secret-key-here"  # Should be from environment
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def hash_password(password: str) -> str:
    """Hash a password for storing"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


async def authenticate_user_async(email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Async-compatible user authentication
    Returns user data with JWT token or None if authentication fails
    """
    try:
        # Run the sync database operations in a thread pool
        loop = asyncio.get_event_loop()
        
        def _sync_auth():
            """Synchronous authentication logic"""
            try:
                # Use the working SimpleDatabaseOperations
                from config import load_config
                database_url = load_config()
                db = SimpleDatabaseOperations(database_url)
                
                # Get user by email
                user = db.get_user_by_email(email)
                
                if not user or not user.password_hash:
                    return None
                
                # Verify password
                if not verify_password(password, user.password_hash):
                    return None
                
                # Update last login (optional - can be done async later)
                # For now, skip to avoid blocking
                
                # Generate JWT token
                jwt_payload = {
                    "user_id": str(user.id),  # Convert UUID to string
                    "email": user.email,
                    "account_type": user.account_type,
                    "role": user.role,
                    "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
                }
                
                jwt_token = jwt.encode(jwt_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
                
                # Return user data with token
                return {
                    "user_id": str(user.id),
                    "email": user.email,
                    "name": user.name,
                    "account_type": user.account_type,
                    "role": user.role,
                    "jwt_token": jwt_token,
                    "email_verified": getattr(user, 'email_verified', True),
                    "rbac_roles": {},  # Simplified for now
                    "is_system_admin": False
                }
                
            except Exception as e:
                logger.error(f"Sync auth error: {e}")
                return None
        
        # Run sync operation in thread pool to avoid blocking
        result = await loop.run_in_executor(None, _sync_auth)
        return result
        
    except Exception as e:
        logger.error(f"Async auth error: {e}")
        return None


# Sync version for backward compatibility
def authenticate_user_sync(email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Synchronous authentication - for direct function calls
    This is the working version we tested earlier
    """
    try:
        from config import load_config
        database_url = load_config()
        db = SimpleDatabaseOperations(database_url)
        
        # Get user by email
        user = db.get_user_by_email(email)
        
        if not user or not user.password_hash:
            return None
        
        # Verify password
        if not verify_password(password, user.password_hash):
            return None
        
        # Generate JWT token
        jwt_payload = {
            "user_id": str(user.id),  # Convert UUID to string
            "email": user.email,
            "account_type": user.account_type,
            "role": user.role,
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        }
        
        jwt_token = jwt.encode(jwt_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        # Return user data with token
        return {
            "user_id": str(user.id),
            "email": user.email,
            "name": user.name,
            "account_type": user.account_type,
            "role": user.role,
            "jwt_token": jwt_token,
            "email_verified": getattr(user, 'email_verified', True),
            "rbac_roles": {},  # Simplified for now
            "is_system_admin": False
        }
        
    except Exception as e:
        logger.error(f"Sync auth error: {e}")
        return None


async def create_user_async(email: str, password: str, name: str, account_type: str = "individual") -> Optional[Dict[str, Any]]:
    """
    Async-compatible user creation
    """
    try:
        loop = asyncio.get_event_loop()
        
        def _sync_create():
            try:
                from config import load_config
                database_url = load_config()
                db = SimpleDatabaseOperations(database_url)
                
                # Hash password
                password_hash = hash_password(password)
                
                # Create user
                user = db.create_user(
                    email=email,
                    name=name,
                    password_hash=password_hash,
                    account_type=account_type,
                    subscription_tier="free",
                    role="user",
                    created_via="api",
                    email_verified=True,
                    is_active=True
                )
                
                return {
                    "user_id": str(user.id),
                    "email": user.email,
                    "name": user.name,
                    "account_type": user.account_type,
                    "role": user.role
                }
                
            except Exception as e:
                logger.error(f"Sync create user error: {e}")
                return None
        
        result = await loop.run_in_executor(None, _sync_create)
        return result
        
    except Exception as e:
        logger.error(f"Async create user error: {e}")
        return None
