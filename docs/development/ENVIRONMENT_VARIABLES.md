# Environment Variables Guide

## JWT Authentication Configuration

### Server-Side Environment Variables

#### `NINAIVALAIGAL_JWT_SECRET` (Server Only)
- **Purpose**: Secret key used by the server to sign and verify JWT tokens
- **Who sets it**: System administrator/deployment team
- **Where**: Server environment only
- **Example**: `export NINAIVALAIGAL_JWT_SECRET="your-production-secret-key-here"`
- **Security**: 🔒 **NEVER commit to git** - This is a server secret
- **Default**: `dev-secret-key-change-in-production` (for development only)

#### `NINAIVALAIGAL_JWT_EXPIRATION_HOURS` (Optional)
- **Purpose**: How long JWT tokens remain valid
- **Default**: 168 hours (7 days)
- **Example**: `export NINAIVALAIGAL_JWT_EXPIRATION_HOURS="24"`

### Client-Side Environment Variables

#### `NINAIVALAIGAL_USER_TOKEN` (Per User)
- **Purpose**: Individual user's JWT token for authentication
- **Who sets it**: Each user after login/signup
- **Where**: User's local environment (shell, IDE, etc.)
- **Example**: `export NINAIVALAIGAL_USER_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."`
- **Security**: 🔐 User-specific, contains user ID and permissions
- **Lifetime**: Expires based on `NINAIVALAIGAL_JWT_EXPIRATION_HOURS`

## How It Works

1. **Server Setup**: Admin sets `NINAIVALAIGAL_JWT_SECRET` on server
2. **User Login**: User authenticates and receives a JWT token
3. **Client Setup**: User sets `NINAIVALAIGAL_USER_TOKEN` in their environment
4. **API Calls**: Client automatically includes token in Authorization header

## Token Structure

JWT tokens contain:
```json
{
  "user_id": 8,
  "email": "user@example.com",
  "account_type": "individual",
  "role": "user",
  "exp": 1757879629
}
```

## Security Best Practices

### For Server Administrators:
- Use a strong, random `NINAIVALAIGAL_JWT_SECRET` in production
- Never commit the JWT secret to version control
- Rotate the secret periodically
- Use environment-specific secrets (dev/staging/prod)

### For Users:
- Keep your `NINAIVALAIGAL_USER_TOKEN` private
- Don't share tokens between users
- Tokens expire automatically for security
- Re-authenticate when tokens expire

## Development vs Production

### Development:
```bash
# Server (temporary for testing)
export NINAIVALAIGAL_JWT_SECRET="dev-secret-key-change-in-production"

# User (after login)
export NINAIVALAIGAL_USER_TOKEN="<your-jwt-token>"
```

### Production:
```bash
# Server (strong secret)
export NINAIVALAIGAL_JWT_SECRET="$(openssl rand -base64 64)"

# User (from login response)
export NINAIVALAIGAL_USER_TOKEN="<token-from-login-api>"
```

## CLI Usage

Once environment variables are set:
```bash
# All commands automatically use the JWT token
eM contexts
eM start --context my-project
eM remember '{"data": "example"}' --context my-project
eM recall --context my-project
```

## Troubleshooting

### "Invalid authentication credentials"
- Check if `NINAIVALAIGAL_USER_TOKEN` is set
- Verify token hasn't expired
- Ensure server and client use same JWT secret

### "Connection refused"
- Verify server is running
- Check if `NINAIVALAIGAL_JWT_SECRET` is set on server
- Confirm server port (default: 13370)
