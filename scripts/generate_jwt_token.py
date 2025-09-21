#!/usr/bin/env python3
"""
JWT Token Generator for Ninaivalaigal Users
Generates JWT tokens for user authentication without sharing database passwords
"""

import sys
from datetime import datetime, timedelta

import jwt

# JWT Secret (should match NINAIVALAIGAL_JWT_SECRET)
JWT_SECRET = "ninaivalaigal-super-secret-jwt-signing-key-min-32-chars-2024"

def generate_user_token(user_id, organization_id, teams=None, role="member", expires_days=30):
    """
    Generate JWT token for a user
    
    Args:
        user_id: Unique user identifier
        organization_id: Organization the user belongs to
        teams: List of teams user belongs to
        role: User role (member, lead, admin)
        expires_days: Token expiration in days
    
    Returns:
        JWT token string
    """
    if teams is None:
        teams = []

    # Token payload
    payload = {
        'user_id': user_id,
        'organization_id': organization_id,
        'teams': teams,
        'role': role,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(days=expires_days)
    }

    # Generate token
    token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
    return token

def decode_token(token):
    """
    Decode and validate JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload or None if invalid
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        print("Token has expired")
        return None
    except jwt.InvalidTokenError:
        print("Invalid token")
        return None

def main():
    """Generate tokens for common test scenarios"""

    print("=== Ninaivalaigal JWT Token Generator ===\n")

    # Example tokens for testing
    test_users = [
        {
            'user_id': 'arun',
            'organization_id': 'acme_corp',
            'teams': [
                {'team_id': 'engineering', 'role': 'lead'},
                {'team_id': 'product', 'role': 'member'}
            ],
            'role': 'admin'
        },
        {
            'user_id': 'sarah',
            'organization_id': 'startup_xyz',
            'teams': [
                {'team_id': 'frontend', 'role': 'member'},
                {'team_id': 'design', 'role': 'lead'}
            ],
            'role': 'member'
        },
        {
            'user_id': 'mike',
            'organization_id': 'acme_corp',
            'teams': [
                {'team_id': 'backend', 'role': 'lead'}
            ],
            'role': 'member'
        }
    ]

    print("Generated JWT Tokens:\n")

    for user in test_users:
        token = generate_user_token(
            user['user_id'],
            user['organization_id'],
            user['teams'],
            user['role']
        )

        print(f"User: {user['user_id']} ({user['organization_id']})")
        print(f"Teams: {[t['team_id'] for t in user['teams']]}")
        print(f"Token: {token}")
        print(f"Length: {len(token)} characters")

        # Verify token
        decoded = decode_token(token)
        if decoded:
            exp_date = datetime.fromtimestamp(decoded['exp'])
            print(f"Expires: {exp_date.strftime('%Y-%m-%d %H:%M:%S')}")

        print("-" * 80)

    # Interactive token generation
    print("\n=== Interactive Token Generation ===")

    if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        while True:
            print("\nEnter user details (or 'quit' to exit):")

            user_id = input("User ID: ").strip()
            if user_id.lower() == 'quit':
                break

            org_id = input("Organization ID: ").strip()
            team_input = input("Teams (comma-separated team_id:role pairs, e.g. 'engineering:lead,product:member'): ").strip()

            teams = []
            if team_input:
                for team_pair in team_input.split(','):
                    if ':' in team_pair:
                        team_id, role = team_pair.strip().split(':', 1)
                        teams.append({'team_id': team_id.strip(), 'role': role.strip()})
                    else:
                        teams.append({'team_id': team_pair.strip(), 'role': 'member'})

            user_role = input("User role (member/lead/admin) [member]: ").strip() or 'member'
            expires_days = input("Expires in days [30]: ").strip()
            expires_days = int(expires_days) if expires_days.isdigit() else 30

            token = generate_user_token(user_id, org_id, teams, user_role, expires_days)

            print("\nGenerated Token:")
            print(f"NINAIVALAIGAL_USER_TOKEN={token}")
            print("\nAdd this to your .vscode/mcp.json or environment variables")

if __name__ == "__main__":
    main()
