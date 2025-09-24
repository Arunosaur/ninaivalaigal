#!/usr/bin/env python3
"""
Create a test JWT token for graph intelligence testing
"""

import os
import sys
from datetime import datetime, timedelta

import jwt

# Add server directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "server"))


def create_test_token():
    """Create a test JWT token"""

    # Set JWT secret (same as used by the API)
    jwt_secret = os.getenv("NINAIVALAIGAL_JWT_SECRET", "test-jwt-secret-for-ci")

    # Create token data for a test user (using UUID)
    token_data = {
        "sub": "00000000-0000-0000-0000-000000000001",  # user_id as UUID
        "email": "test@ninaivalaigal.com",
        "user_id": "00000000-0000-0000-0000-000000000001",
        "exp": datetime.utcnow() + timedelta(hours=24),  # 24 hour expiration
    }

    # Create JWT token
    token = jwt.encode(token_data, jwt_secret, algorithm="HS256")

    print(f"Test JWT Token: {token}")
    print(f"Expires: {token_data['exp']}")
    print(f"User ID: {token_data['user_id']}")
    print(f"Email: {token_data['email']}")

    return token


if __name__ == "__main__":
    create_test_token()
