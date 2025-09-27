# Mem0 User Signup and Authentication System

## Overview

The mem0 signup system supports three types of users:
- **Individual Users**: Personal AI memory for solo development
- **Organization Admins**: Full organization management capabilities
- **Team Members**: Collaborative memory with team access (via invitation)

## API Endpoints

### Individual User Signup
```bash
POST /auth/signup/individual
Content-Type: application/json

{
  "email": "user@example.com",
  "password  # pragma: allowlist secret": "SecurePass123",
  "name": "John Doe"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Individual user account created successfully",
  "user": {
    "user_id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "account_type": "individual",
    "personal_contexts_limit": 10,
    "jwt_token  # pragma: allowlist secret": "eyJ...",
    "email_verified": false
  },
  "next_steps": ["verify_email", "create_first_context", "install_tools"]
}
```

### Organization Signup
```bash
POST /auth/signup/organization
Content-Type: application/json

{
  "user": {
    "email": "admin@company.com",
    "password  # pragma: allowlist secret": "AdminPass123",
    "name": "Jane Admin"
  },
  "organization": {
    "name": "Acme Corporation",
    "domain": "company.com",
    "size": "51-200",
    "industry": "Technology"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Organization and admin account created successfully",
  "user_id": 2,
  "organization_id": 1,
  "role": "organization_admin",
  "jwt_token  # pragma: allowlist secret": "eyJ...",
  "setup_steps": ["verify_email", "setup_teams", "invite_members", "create_org_contexts"]
}
```

### User Login
```bash
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password  # pragma: allowlist secret": "SecurePass123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "user": {
    "user_id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "account_type": "individual",
    "role": "user",
    "jwt_token  # pragma: allowlist secret": "eyJ...",
    "email_verified": false
  }
}
```

### Email Verification
```bash
GET /auth/verify-email?token  # pragma: allowlist secret=verification_token
```

### User Information
```bash
GET /auth/me
Authorization: Bearer <jwt_token  # pragma: allowlist secret>
```

## Frontend Pages

### Signup Page
- **Location**: `/frontend/signup.html`
- **Features**:
  - Account type selection (Individual vs Organization)
  - Dynamic form switching
  - Client-side validation
  - Loading and success states
  - Error handling

### Login Page
- **Location**: `/frontend/login.html`
- **Features**:
  - Email/password  # pragma: allowlist secret authentication
  - Remember me option
  - Forgot password  # pragma: allowlist secret link
  - Account type information
  - Automatic redirect after login

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    password  # pragma: allowlist secret_hash VARCHAR(255) NOT NULL,
    account_type VARCHAR(50) NOT NULL DEFAULT 'individual',
    subscription_tier VARCHAR(50) NOT NULL DEFAULT 'free',
    personal_contexts_limit INTEGER DEFAULT 10,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    created_via VARCHAR(50) NOT NULL DEFAULT 'signup',
    email_verified BOOLEAN DEFAULT FALSE,
    verification_token  # pragma: allowlist secret VARCHAR(255),
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Organizations Table
```sql
CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    domain VARCHAR(255),
    settings JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Organization Registrations Table
```sql
CREATE TABLE organization_registrations (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id),
    creator_user_id INTEGER REFERENCES users(id),
    registration_data JSON,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    billing_email VARCHAR(255) NOT NULL,
    company_size VARCHAR(50),
    industry VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### User Invitations Table
```sql
CREATE TABLE user_invitations (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    organization_id INTEGER REFERENCES organizations(id),
    team_id INTEGER REFERENCES teams(id),
    invited_by INTEGER REFERENCES users(id),
    invitation_token  # pragma: allowlist secret VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    expires_at TIMESTAMP NOT NULL,
    accepted_at TIMESTAMP,
    invitation_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Memory Architecture

### Individual Users
- **Personal Contexts**: Up to 10 contexts (free tier)
- **Memory Scope**: Private to user only
- **Access Pattern**: Direct user-owned memories

### Team Members
- **Personal Contexts**: Individual memories
- **Team Contexts**: Shared team memories
- **Memory Scope**: Personal + assigned teams
- **Access Pattern**: Hierarchical (Personal → Team)

### Organization Admins
- **Personal Contexts**: Individual memories
- **Team Contexts**: All organization teams
- **Organization Contexts**: Organization-wide memories
- **Memory Scope**: Personal + Team + Organization
- **Access Pattern**: Hierarchical (Personal → Team → Organization)

## Security Features

### Password Requirements
- Minimum 8 characters
- Must contain letters and numbers
- Hashed using bcrypt

### JWT Authentication
- 24-hour token  # pragma: allowlist secret expiration
- Includes user_id, email, account_type, role
- Environment-configurable secret key

### Email Verification
- Required for account activation
- Secure token  # pragma: allowlist secret-based verification
- Placeholder implementation (needs email service integration)

## Testing

### Automated Tests
Run the test suite:
```bash
cd /Users/asrajag/Workspace/mem0
python test_signup.py
```

### Manual Testing
1. **Individual Signup**: Visit `http://localhost:8000/frontend/signup.html`
2. **Organization Signup**: Select organization option on signup page
3. **Login**: Visit `http://localhost:8000/frontend/login.html`
4. **API Testing**: Use curl commands or Postman with the API endpoints

## Configuration

### Environment Variables
```bash
export MEM0_DATABASE_URL="postgresql://mem0user:mem0pass@localhost:5432/mem0db"
export MEM0_JWT_SECRET="your-secret-key-here"
export MEM0_USER_ID="1"  # For context association
```

### Database Setup
1. Ensure PostgreSQL is running
2. Run schema migrations:
```bash
cd /Users/asrajag/Workspace/mem0/scripts
psql postgresql://mem0user:mem0pass@localhost:5432/mem0db -f create-user-management-schema.sql
```

## Deployment

### Local Development
```bash
cd /Users/asrajag/Workspace/mem0/server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Production Considerations
- Use strong JWT secrets
- Implement proper email service (SendGrid, AWS SES)
- Set up SSL/TLS certificates
- Configure rate limiting
- Enable audit logging
- Set up monitoring and alerts

## Next Steps

1. **Email Integration**: Replace placeholder email verification with actual service
2. **Team Invitations**: Complete invitation flow implementation
3. **Admin Dashboard**: Build organization management UI
4. **Memory Scoping**: Implement context-based memory isolation
5. **Subscription Management**: Add billing and plan management
6. **Advanced Security**: Add 2FA, password  # pragma: allowlist secret reset, account lockout

## Troubleshooting

### Common Issues

**Database Connection Errors**:
- Verify PostgreSQL is running
- Check connection string in environment variables
- Ensure database exists and user has permissions

**Missing Database Columns**:
- Run the schema migration script
- Check if all required columns exist in users/organizations tables

**JWT Token Issues**:
- Verify JWT_SECRET is set
- Check token  # pragma: allowlist secret expiration (24 hours default)
- Ensure Authorization header format: `Bearer <token  # pragma: allowlist secret>`

**Email Verification Not Working**:
- Currently uses placeholder implementation
- Check console logs for verification URLs
- Implement actual email service for production

### Support

For issues or questions:
1. Check the logs in the server console
2. Verify database schema matches expected structure
3. Test API endpoints directly with curl
4. Review the test suite for expected behavior patterns
