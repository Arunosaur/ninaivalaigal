# 🏢 How to Sign Up for Organization

## ✅ **Organization Signup is Now Available!**

You can now create organization accounts directly from the UI! Here's how:

---

## **Step-by-Step Guide**

### **1. Navigate to Signup Page**
- Go to: http://localhost:8101/signup
- Or click "Sign up" from the login page

### **2. Select Account Type**
You'll see two buttons at the top:
- **👤 Individual** - For personal use (default)
- **🏢 Organization** - For companies and teams

Click **🏢 Organization**

### **3. Fill in Your Details**

#### **Personal Information** (Required for all):
- **Your Name**: Your full name (e.g., Jane Smith)
- **Email**: Your work email (e.g., jane@acmecorp.com)
- **Password**: Secure password with 8+ characters

#### **Organization Information** (When Organization is selected):
- **Organization Name** * (Required): Company name (e.g., Acme Corporation)
- **Organization Domain** (Optional): Company domain (e.g., acmecorp.com)
- **Company Size** (Optional): Select from dropdown:
  - 1-10
  - 11-50
  - 51-200
  - 201-500
  - 501+
- **Industry** (Optional): Select from dropdown:
  - Technology
  - Healthcare
  - Finance
  - Education
  - Retail
  - Manufacturing
  - Other

### **4. Submit**
Click **"Sign Up as Organization"** button

### **5. Automatic Login**
Upon successful signup, you'll be:
- Automatically logged in
- Redirected to your Dashboard
- Ready to create teams and invite members!

---

## **Example Organization Signup**

```
Account Type: 🏢 Organization

Your Name: Jane Smith
Email: jane@acmecorp.com
Password: SecurePass123!  # pragma: allowlist secret

Organization Name: Acme Corporation
Organization Domain: acmecorp.com
Company Size: 51-200
Industry: Technology
```

**Result**: Creates organization account with Jane as the admin

---

## **What Happens After Organization Signup?**

### **As Organization Admin, You Can:**

1. **Create Teams**
   - Navigate to Teams section
   - Create multiple teams (Engineering, Sales, Marketing, etc.)
   - Assign team leaders

2. **Invite Team Members**
   - Send email invitations
   - Set roles (Admin, Member, Viewer)
   - Manage permissions

3. **Configure RBAC**
   - Set up role-based access control
   - Define policies for each team
   - Control who can access what

4. **View Organization Dashboard**
   - Organization-wide statistics
   - All teams at a glance
   - Usage analytics

---

## **Individual vs Organization Comparison**

| Feature | Individual 👤 | Organization 🏢 |
|---------|--------------|----------------|
| **Personal Memories** | ✅ Yes | ✅ Yes |
| **Teams** | ❌ No | ✅ Yes |
| **Team Collaboration** | ❌ No | ✅ Yes |
| **Multiple Users** | ❌ No | ✅ Yes |
| **RBAC Policies** | ❌ No | ✅ Yes |
| **Organization Dashboard** | ❌ No | ✅ Yes |
| **Shared Workspaces** | ❌ No | ✅ Yes |
| **Usage Analytics** | Basic | ✅ Advanced |

---

## **API Endpoints**

### **Organization Signup**
```bash
POST /auth/signup/organization
Content-Type: application/json

{
  "email": "jane@acmecorp.com",
  "password": "SecurePass123!",  # pragma: allowlist secret
  "full_name": "Jane Smith",
  "organization_name": "Acme Corporation",
  "organization_domain": "acmecorp.com",
  "organization_size": "51-200",
  "organization_industry": "Technology"
}
```

### **Individual Signup** (Existing)
```bash
POST /auth/signup/individual
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "SecurePass123!",  # pragma: allowlist secret
  "full_name": "John Doe"
}
```

---

## **Quick Test: Create Organization via UI**

1. **Logout** if currently logged in:
   - Click "Logout" in top-right corner

2. **Go to Signup**:
   ```
   http://localhost:8101/signup
   ```

3. **Fill the Form**:
   - Click **🏢 Organization** button
   - Name: Your Name
   - Email: your-work-email@company.com
   - Password: YourSecurePassword123!  # pragma: allowlist secret
   - Organization Name: Your Company Name
   - Organization Domain: company.com
   - Company Size: 51-200
   - Industry: Technology

4. **Click "Sign Up as Organization"**

5. **Success!** You're now an organization admin!

---

## **Next Steps After Creating Organization**

### **Immediate Actions:**
1. ✅ **Explore Dashboard** - See organization overview
2. ✅ **Create First Team** - Set up Engineering/Sales/Marketing team
3. ✅ **Invite Members** - Send invites to teammates
4. ✅ **Create Memories** - Start capturing organizational knowledge

### **Advanced Configuration:**
1. 🔧 **Set up RBAC Policies** - Define access controls
2. 🔧 **Configure Team Settings** - Customize each team
3. 🔧 **Enable Integrations** - Connect Slack, GitHub, etc.
4. 🔧 **Set Usage Limits** - Control resource allocation

---

## **Troubleshooting**

### **"Organization name already exists"**
- Try a different organization name
- Check if your organization already has an account

### **"Email already registered"**
- Use a different email address
- Or login if you already have an account

### **"Invalid password"**
- Password must be at least 8 characters
- Include uppercase, lowercase, numbers, and special characters

### **Can't see organization fields?**
- Make sure you clicked **🏢 Organization** button
- Button should be highlighted in indigo/purple color
- Form should expand to show additional fields

---

## **Screenshots**

### **Individual Mode** (Default)
- Shows: Name, Email, Password
- Button: "Sign Up as Individual"

### **Organization Mode** (After clicking 🏢 Organization)
- Shows all fields including:
  - Organization Name
  - Organization Domain
  - Company Size dropdown
  - Industry dropdown
- Button: "Sign Up as Organization"

---

## **Summary**

✅ **Organization signup is fully functional**
✅ **Easy-to-use UI with account type selector**
✅ **All fields properly validated**
✅ **Automatic login after signup**
✅ **Ready to create teams and collaborate!**

**You can now sign up for organizations directly from the UI - no need for curl commands!** 🎉
