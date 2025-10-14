---
{}
---




## 2) Core Concepts

### Staff vs Customer Separation
- **Staff**: Platform employees (support, ops, analyst, admin)
- **Customers**: End users (individuals, teams, orgs)
- **Separate Tables**: No mixing of staff and customer data
- **Separate Authentication**: Staff login via admin console only

### Staff Roles
1. **Support**: Customer assistance, ticket resolution, basic troubleshooting
2. **Operations**: Platform monitoring, maintenance, incident response
3. **Analyst**: Business intelligence, reporting, data analysis
4. **Admin**: Full platform management, staff management, system configuration

---

## 3) Database Schema

### Staff Table
```sql
CREATE TABLE staff (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('support', 'ops', 'analyst', 'admin')),
    department VARCHAR(100),
    phone VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES staff(id),
    last_login TIMESTAMP,
    last_login_ip VARCHAR(45),
    is_active BOOLEAN DEFAULT true,
    deactivated_at TIMESTAMP,
    deactivated_by UUID REFERENCES staff(id),
    notes TEXT
);

CREATE INDEX idx_staff_email ON staff(email);
CREATE INDEX idx_staff_role ON staff(role);
CREATE INDEX idx_staff_active ON staff(is_active);
```

### Staff Activity Log
```sql
CREATE TABLE staff_activity_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    staff_id UUID REFERENCES staff(id) NOT NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    details JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_staff_activity_staff ON staff_activity_log(staff_id);
CREATE INDEX idx_staff_activity_created ON staff_activity_log(created_at);
CREATE INDEX idx_staff_activity_action ON staff_activity_log(action);
```

### Staff Permissions
```sql
CREATE TABLE staff_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    staff_id UUID REFERENCES staff(id) NOT NULL,
    permission VARCHAR(100) NOT NULL,
    granted_by UUID REFERENCES staff(id),
    granted_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    UNIQUE(staff_id, permission)
);

CREATE INDEX idx_staff_permissions_staff ON staff_permissions(staff_id);
```

---

## 4) Role Permissions Matrix

### Support Role
- ✅ View customer accounts
- ✅ View support tickets
- ✅ Update ticket status
- ✅ View basic analytics
- ❌ Cannot modify billing
- ❌ Cannot access admin functions
- ❌ Cannot manage staff

### Operations Role
- ✅ View system metrics
- ✅ Restart services
- ✅ View logs
- ✅ Manage infrastructure
- ✅ View all customer data (read-only)
- ❌ Cannot modify customer billing
- ❌ Cannot manage staff

### Analyst Role
- ✅ View all analytics
- ✅ Generate reports
- ✅ Export data
- ✅ View customer usage patterns
- ❌ Cannot modify customer data
- ❌ Cannot manage infrastructure
- ❌ Cannot manage staff

### Admin Role
- ✅ Full platform access
- ✅ Manage staff accounts
- ✅ Assign roles and permissions
- ✅ View all audit logs
- ✅ Modify system configuration
- ✅ Access all features

---

## 5) Staff Creation Process (Option A: Manual)

### Step 1: Admin Creates Staff Account
```
Admin Console → Staff Management → Create Staff
- Enter: Name, Email, Role, Department
- System generates temporary password
- Account created in "pending" state
```

### Step 2: Temporary Password Delivery
```
- Email sent to staff member with:
  - Temporary password (expires in 24 hours)
  - Link to staff login page
  - Instructions for first login
- Email logged in audit trail
```

### Step 3: First Login & Password Reset
```
- Staff logs in with temporary password
- Forced to set new password (min 12 chars, complexity rules)
- Account activated
- First login logged
```

### Step 4: Account Active
```
- Staff can access admin console
- All actions logged
- Regular password rotation required (90 days)
```

---

## 6) API Endpoints

### Staff Management (Admin Only)

#### Create Staff
```
POST /admin/staff
Authorization: Bearer <admin_token>
Body: {
  "name": "Jane Smith",
  "email": "jane@ninaivalaigal.com",
  "role": "support",
  "department": "Customer Success"
}
Response: {
  "staff_id": "uuid",
  "temporary_password": "temp_pass_123",
  "expires_at": "2024-10-04T10:00:00Z"
}
```

#### List Staff
```
GET /admin/staff?role=support&active=true
Authorization: Bearer <admin_token>
Response: {
  "staff": [
    {
      "id": "uuid",
      "name": "Jane Smith",
      "email": "jane@ninaivalaigal.com",
      "role": "support",
      "department": "Customer Success",
      "is_active": true,
      "last_login": "2024-10-03T09:00:00Z"
    }
  ],
  "total": 15,
  "page": 1
}
```

#### Update Staff Role
```
PUT /admin/staff/{staff_id}/role
Authorization: Bearer <admin_token>
Body: {
  "role": "ops",
  "reason": "Promoted to operations team"
}
Response: {
  "success": true,
  "staff_id": "uuid",
  "old_role": "support",
  "new_role": "ops"
}
```

#### Deactivate Staff
```
DELETE /admin/staff/{staff_id}
Authorization: Bearer <admin_token>
Body: {
  "reason": "Employee left company"
}
Response: {
  "success": true,
  "deactivated_at": "2024-10-03T10:00:00Z"
}
```

#### View Staff Activity
```
GET /admin/staff/{staff_id}/activity?days=30
Authorization: Bearer <admin_token>
Response: {
  "activity": [
    {
      "action": "view_customer",
      "resource_id": "customer_123",
      "timestamp": "2024-10-03T09:30:00Z",
      "ip_address": "192.168.1.1"
    }
  ]
}
```

### Staff Authentication

#### Staff Login
```
POST /auth/staff/login
Body: {
  "email": "jane@ninaivalaigal.com",
  "password": "secure_password"
}
Response: {
  "access_token": "jwt_token",
  "role": "support",
  "permissions": ["view_customers", "update_tickets"],
  "requires_password_reset": false
}
```

#### Reset Password
```
POST /auth/staff/reset-password
Authorization: Bearer <staff_token>
Body: {
  "current_password": "old_pass",
  "new_password": "new_secure_pass"
}
Response: {
  "success": true,
  "message": "Password updated successfully"
}
```

---

## 7) Admin Console UI

### Staff Management Page (`staff-management.html`)

#### Features:
- **Staff List**: Searchable, filterable table
- **Create Staff**: Modal form
- **Edit Staff**: Update role, department
- **Deactivate**: Soft delete with reason
- **Activity Log**: View staff actions
- **Bulk Actions**: Deactivate multiple staff

#### UI Components:
```
┌─────────────────────────────────────────────────┐
│ Staff Management                    [+ Add Staff]│
├─────────────────────────────────────────────────┤
│ Search: [___________]  Role: [All ▼]  Active: ✓ │
├─────────────────────────────────────────────────┤
│ Name          Email           Role      Actions  │
│ Jane Smith    jane@...       Support   [Edit][X] │
│ John Doe      john@...       Ops       [Edit][X] │
│ Alice Brown   alice@...      Admin     [Edit][X] │
└─────────────────────────────────────────────────┘
```

---

## 8) Security Measures

### Password Requirements
- Minimum 12 characters
- Must include: uppercase, lowercase, number, special char
- Cannot reuse last 5 passwords
- Expires every 90 days
- Temporary passwords expire in 24 hours

### Access Control
- All staff actions logged
- IP address tracking
- Failed login attempts monitored (5 attempts = 15min lockout)
- Session timeout: 8 hours
- Require re-authentication for sensitive actions

### Audit Trail
- Every staff action logged with:
  - Who (staff_id)
  - What (action)
  - When (timestamp)
  - Where (IP address)
  - Why (reason, if applicable)

---

## 9) Email Templates

### Welcome Email
```
Subject: Welcome to Ninaivalaigal Platform Team

Hi {name},

You've been added to the Ninaivalaigal platform team as a {role}.

Temporary Password: {temp_password}
Login URL: https://admin.ninaivalaigal.com/staff-login

This password expires in 24 hours. Please log in and set a new password.

Role: {role}
Department: {department}

If you have questions, contact IT support.

- Ninaivalaigal Platform Team
```

### Password Expiry Warning
```
Subject: Password Expiring Soon

Hi {name},

Your password will expire in {days} days. Please reset it to avoid account lockout.

Reset Password: https://admin.ninaivalaigal.com/reset-password

- Ninaivalaigal Security Team
```

---

## 10) Implementation Checklist

- [ ] Create database schema (staff, staff_activity_log, staff_permissions)
- [ ] Implement API endpoints (/admin/staff/*)
- [ ] Create staff authentication endpoints (/auth/staff/*)
- [ ] Build staff management UI (staff-management.html)
- [ ] Implement email notifications
- [ ] Add password complexity validation
- [ ] Create audit logging middleware
- [ ] Add role-based access control (RBAC)
- [ ] Write integration tests
- [ ] Document staff onboarding process

---

## 11) Success Metrics

- ✅ Staff can be created via admin console
- ✅ Temporary passwords sent via email
- ✅ Staff can log in and reset password
- ✅ Role-based permissions enforced
- ✅ All staff actions logged
- ✅ Admins can view staff activity
- ✅ Deactivated staff cannot log in

---

**Next Steps:**
1. Approve SPEC-085
2. Create database migration
3. Implement API endpoints
4. Build admin console UI
5. Test staff creation workflow
6. Deploy to staging
