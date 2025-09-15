"""
Authentication and user management for Ninaivalaigal
Supports individual users, team members, and organization creators
"""

import os
import jwt
import bcrypt
import secrets
import smtplib
import json
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from input_validation import get_api_validator, InputValidationError
from email.mime.multipart import MIMEMultipart

# Configuration loading (moved from main.py to avoid circular import)
def load_config():
    config_path = "../ninaivalaigal.config.json"
    default_config = {
        "storage": {
            "database_url": "postgresql://mem0user:mem0pass@localhost:5432/mem0db"
        }
    }
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                if "storage" in user_config and "database_url" in user_config["storage"]:
                    return user_config["storage"]["database_url"]
        return default_config["storage"]["database_url"]
    except Exception:
        return default_config["storage"]["database_url"]

# Database helper to avoid circular imports
def get_db():
    """Get database instance"""
    from database import DatabaseManager
    database_url = load_config()  # load_config returns string directly
    return DatabaseManager(database_url)

# JWT Secret from environment (REQUIRED - no fallback for security)
JWT_SECRET = os.getenv('NINAIVALAIGAL_JWT_SECRET')
if not JWT_SECRET:
    raise ValueError("NINAIVALAIGAL_JWT_SECRET environment variable is required for security")
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = int(os.getenv('NINAIVALAIGAL_JWT_EXPIRATION_HOURS', '168'))  # Default 7 days

# Password validation
def validate_password(password: str) -> bool:
    """Validate password strength"""
    if len(password) < 8:
        return False
    if not re.search(r'[A-Za-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    return True

# Email validation
def validate_email(email: str) -> bool:
    """Basic email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Password hashing
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# Token generation
def generate_verification_token() -> str:
    """Generate secure verification token"""
    return secrets.token_urlsafe(32)

def generate_invitation_token() -> str:
    """Generate secure invitation token"""
    return secrets.token_urlsafe(32)

# Pydantic models for signup and auth
class IndividualUserSignup(BaseModel):
    email: EmailStr
    password: str
    name: str
    account_type: str = "individual"

class OrganizationSignup(BaseModel):
    user: Dict[str, Any]  # email, password, name
    organization: Dict[str, Any]  # name, domain, size, industry

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class InvitationAccept(BaseModel):
    invitation_token: str
    user: Dict[str, Any]  # password, name

class UserInvitation(BaseModel):
    email: EmailStr
    team_ids: Optional[list] = []
    role: str = "user"
    message: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None

# Security scheme
security = HTTPBearer()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> TokenData:
    """Verify JWT token and return token data"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("email")  # Use email as username
        user_id: int = payload.get("user_id")
        if username is None or user_id is None:
            return None
        token_data = TokenData(username=username, user_id=user_id)
    except jwt.InvalidTokenError:
        return None
    return token_data

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    token_data = verify_token(credentials.credentials)
    if token_data is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    # Get user from database
    db = get_db()
    user = db.get_user_by_id(token_data.user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user

async def get_current_user_optional(request: Request):
    """Get current user if authenticated, None otherwise"""
    try:
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]
        token_data = verify_token(token)

        user = db.get_user_by_id(token_data.user_id)
        return user
    except:
        return None

# User management functions
def create_individual_user(signup_data):
    """Create individual user account"""
    # Validate email and password
    try:
        # Validate input data
        api_validator = get_api_validator()
        validated_data = api_validator.validate_signup_data({
            'email': signup_data.email,
            'password': signup_data.password,
            'name': signup_data.name,
            'account_type': signup_data.account_type
        })
        
        db = get_db()
        
        # Check if user already exists
        existing_user = db.get_user_by_email(validated_data['email'])
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Hash password
        hashed_password = hash_password(validated_data['password'])
        
        # Create user
        new_user = db.create_user(
            email=validated_data['email'],
            password_hash=hashed_password,
            name=validated_data['name'],
            account_type=validated_data['account_type']
        )
        
        session.add(new_user)
        session.commit()
        
        # Generate JWT token
        jwt_payload = {
            "user_id": new_user.id,
            "email": new_user.email,
            "account_type": new_user.account_type,
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        }
        jwt_token = jwt.encode(jwt_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        return {
            "user_id": new_user.id,
            "email": new_user.email,
            "name": new_user.name,
            "account_type": new_user.account_type,
            "personal_contexts_limit": new_user.personal_contexts_limit,
            "jwt_token": jwt_token,
            "email_verified": False,
            "verification_token": verification_token
        }
        
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")
    finally:
        session.close()

def authenticate_user(email: str, password: str):
    """Authenticate user login"""
    db = get_db()
    session = db.get_session()
    try:
        from database import User
        user = session.query(User).filter_by(email=email, is_active=True).first()
        
        if not user or not user.password_hash:
            return None
            
        if not verify_password(password, user.password_hash):
            return None
            
        # Update last login
        user.last_login = datetime.utcnow()
        session.commit()
        
        # Generate JWT token
        jwt_payload = {
            "user_id": user.id,
            "email": user.email,
            "account_type": user.account_type,
            "role": user.role,
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        }
        jwt_token = jwt.encode(jwt_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        return {
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "account_type": user.account_type,
            "role": user.role,
            "jwt_token": jwt_token,
            "email_verified": user.email_verified
        }
        
    finally:
        session.close()

def send_verification_email(email: str, verification_token: str):
    """Send email verification (placeholder - implement with actual email service)"""
    # In production, integrate with SendGrid, AWS SES, etc.
    verification_url = f"http://localhost:8000/auth/verify-email?token={verification_token}"
    print(f"Email verification URL for {email}: {verification_url}")
    # TODO: Implement actual email sending

def verify_email_token(verification_token: str) -> bool:
    """Verify email verification token"""
    db = get_db()
    session = db.get_session()
    try:
        from database import User
        user = session.query(User).filter_by(verification_token=verification_token).first()
        
        if not user:
            return False
            
        user.email_verified = True
        user.verification_token = None
        session.commit()
        
        return True
        
    except Exception:
        session.rollback()
        return False
    finally:
        session.close()

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
