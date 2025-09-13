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
from email.mime.multipart import MIMEMultipart

# Configuration loading (moved from main.py to avoid circular import)
def load_config():
    config_path = "../ninaivalaigal.config.json"
    default_config = {
        "storage": {
            "database_url": "sqlite:///./ninaivalaigal.db"
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

# JWT Secret from environment or default
JWT_SECRET = os.getenv('NINAIVALAIGAL_JWT_SECRET', 'dev-secret-key-change-in-production')
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
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> TokenData:
    """Verify JWT token and return token data"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        # Check if user already exists
        db = get_db()
        session = db.get_session()
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        token_data = TokenData(username=username, user_id=user_id)
    except jwt.JWTError:
        return None
    return token_data

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    token_data = verify_token(credentials.credentials)

    # Get user from database
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
    if not validate_email(signup_data.email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    if not validate_password(signup_data.password):
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters with letters and numbers")
    
    # Check if user already exists
    db = get_db()
    session = db.get_session()
    try:
        from database import User
        existing_user = session.query(User).filter_by(email=signup_data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        # Create user
        password_hash = hash_password(signup_data.password)
        verification_token = generate_verification_token()
        
        new_user = User(
            email=signup_data.email,
            name=signup_data.name,
            password_hash=password_hash,
            account_type="individual",
            subscription_tier="free",
            personal_contexts_limit=10,
            created_via="signup",
            email_verified=False,
            verification_token=verification_token,
            role="user"
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
        if "already exists" in str(e):
            raise e
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
