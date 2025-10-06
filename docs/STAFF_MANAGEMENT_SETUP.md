# Staff Management System Setup Guide - SPEC-085

## Overview

The staff management system provides secure, role-based access control for platform operations. This guide covers setup, usage, and administration.

## Quick Start

### 1. Prerequisites

```bash
# Ensure conda environment is active
conda activate nina

# Ensure database is running
make docker-dev-up
```

### 2. Run Migration

```bash
# Run staff management migration
make migrate-staff
```

This creates three tables:
- `staff` - Staff accounts with roles and permissions
- `staff_activity_log` - Audit trail of all staff actions
- `staff_permissions` - Granular permission management

### 3. Seed Initial Admin

```bash
# Create initial admin account
make seed-staff
```

**Default Credentials:**
- Email: `admin@ninaivalaigal.com`
- Password: `ChangeMe123!@#`
- Role: `admin`

⚠️ **IMPORTANT**: Change this password immediately after first login!

### 4. Access Admin Console

```bash
# Admin console is available at:
http://localhost:8181/staff-login.html
```

## Staff Roles

### Support
- View customer accounts
- View and update support tickets
- View basic analytics
- ❌ Cannot modify billing
- ❌ Cannot access admin functions

### Operations (Ops)
- View system metrics
- Restart services
- View logs
- Manage infrastructure
- View all customer data (read-only)
- ❌ Cannot modify customer billing

### Analyst
- View all analytics
- Generate reports
- Export data
- View customer usage patterns
- ❌ Cannot modify customer data
- ❌ Cannot manage infrastructure

### Admin
- ✅ Full platform access
- ✅ Manage staff accounts
- ✅ Assign roles and permissions
- ✅ View all audit logs
- ✅ Modify system configuration

## Environment Variables

### Production Setup

```bash
# .env.production
INITIAL_ADMIN_EMAIL=admin@yourcompany.com
INITIAL_ADMIN_PASSWORD=SecurePassword123!
INITIAL_ADMIN_NAME=Platform Administrator
```

### Security Best Practices

1. **Never commit credentials** to version control
2. **Use strong passwords** (min 12 chars, complexity required)
3. **Rotate passwords** every 90 days
4. **Use SSO** for production environments
5. **Monitor audit logs** regularly

## API Endpoints

### Staff Management (Admin Only)

#### Create Staff
```bash
POST /admin/staff
Authorization: Bearer <admin_token>

{
  "name": "Jane Smith",
  "email": "jane@company.com",
  "role": "support",
  "department": "Customer Success",
  "phone": "+1-555-0123"
}
```

#### List Staff
```bash
GET /admin/staff?role=support&active=true
Authorization: Bearer <admin_token>
```

#### Update Role
```bash
PUT /admin/staff/{staff_id}/role
Authorization: Bearer <admin_token>

{
  "role": "ops",
  "reason": "Promoted to operations team"
}
```

#### Deactivate Staff
```bash
DELETE /admin/staff/{staff_id}
Authorization: Bearer <admin_token>

{
  "reason": "Employee left company"
}
```

#### View Activity
```bash
GET /admin/staff/{staff_id}/activity?days=30
Authorization: Bearer <admin_token>
```

### Staff Authentication

#### Login
```bash
POST /auth/staff/login

{
  "email": "jane@company.com",
  "password": "secure_password"
}

Response:
{
  "access_token": "jwt_token",
  "role": "support",
  "permissions": ["view_customers", "update_tickets"],
  "requires_password_reset": false
}
```

## Admin Console Features

### Staff Management Page

Access: `http://localhost:8181/staff-management.html`

Features:
- **Search & Filter**: Find staff by name, email, role, or status
- **Create Staff**: Add new staff with role assignment
- **View Activity**: See all actions by staff member
- **Deactivate**: Soft delete with reason tracking
- **Temporary Passwords**: Auto-generated secure passwords

### Staff Login Page

Access: `http://localhost:8181/staff-login.html`

Features:
- Distinct from customer login (visual separation)
- SSO integration option
- Security notice and role information
- Failed login tracking (5 attempts = 15min lockout)

## Makefile Commands

```bash
# Run migration
make migrate-staff

# Seed initial admin
make seed-staff

# Complete setup (migrate + seed)
make setup-staff

# Check staff accounts
make check-staff
```

## Troubleshooting

### Migration Fails

```bash
# Check if alembic is installed
conda run -n nina pip list | grep alembic

# Check database connection
conda run -n nina python -c "from sqlalchemy import create_engine; import os; engine = create_engine(os.getenv('DATABASE_URL')); print(engine.connect())"
```

### Seed Script Fails

```bash
# Ensure conda environment is active
conda activate nina

# Run with verbose output
python scripts/seed_initial_staff.py
```

### Cannot Login

1. **Check credentials**: Ensure you're using the correct email/password
2. **Check staff table**: `make check-staff`
3. **Check logs**: Look for authentication errors in API logs
4. **Verify JWT secret**: Ensure SECRET_KEY is set in environment

### Admin Console Not Loading

1. **Check container**: `docker ps | grep admin-console`
2. **Check logs**: `docker logs ninaivalaigal-dev-admin-console`
3. **Rebuild**: `docker-compose -f compose.docker.yml build admin-console`
4. **Restart**: `make docker-dev-up-internal`

## Security Considerations

### Password Requirements
- Minimum 12 characters
- Must include: uppercase, lowercase, number, special char
- Cannot reuse last 5 passwords
- Expires every 90 days
- Temporary passwords expire in 24 hours

### Access Control
- All staff actions logged with IP address
- Failed login attempts monitored
- Session timeout: 8 hours
- Re-authentication required for sensitive actions

### Audit Trail
Every staff action logs:
- **Who**: staff_id
- **What**: action type
- **When**: timestamp
- **Where**: IP address
- **Why**: reason (if applicable)

## Production Deployment

### 1. Update Environment Variables

```bash
# Production .env
INITIAL_ADMIN_EMAIL=admin@production.com
INITIAL_ADMIN_PASSWORD=$(openssl rand -base64 32)
DATABASE_URL=postgresql://user:pass@prod-db:5432/ninaivalaigal
SECRET_KEY=$(openssl rand -hex 32)
```

### 2. Run Migration

```bash
# On production server
conda activate nina
alembic upgrade head
```

### 3. Seed Admin

```bash
# On production server
python scripts/seed_initial_staff.py
```

### 4. Configure SSO (Recommended)

Update `staff-login.html` to use your SSO provider:
- OAuth 2.0
- SAML
- Tailscale SSO
- Auth0 / Okta

### 5. Enable HTTPS

Ensure admin console is only accessible via HTTPS in production.

## Next Steps

1. ✅ Login to admin console
2. ✅ Change default password
3. ✅ Create additional staff accounts
4. ✅ Assign appropriate roles
5. ✅ Configure SSO (production)
6. ✅ Set up monitoring and alerts

## Support

For issues or questions:
- Check logs: `docker logs ninaivalaigal-dev-api`
- Review audit trail: `GET /admin/staff/{id}/activity`
- Contact platform team

---

**SPEC-085: Staff Management System** - Complete ✅
