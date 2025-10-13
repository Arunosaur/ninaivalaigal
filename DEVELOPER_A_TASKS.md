# Developer A - Task Assignment (When You Return)

**Date:** October 12, 2025
**Status:** ⏸️ PAUSED - Return When Ready
**Focus:** Frontend Integration & UI Testing
**Risk Level:** ⚠️ MEDIUM (Frontend files only)

---

## 🎯 Your Mission (When You Return)

Integrate JWT authentication into the frontend UI and add frontend tests.

**Working Directory:** `frontend/`, `ui/`, `web/`
**No Backend Changes:** Frontend only
**Duration:** 4-6 hours

---

## ✅ Task 1: Add JWT Token Storage to Frontend

**Files to Modify:**
- `frontend/src/auth/AuthContext.jsx` (or equivalent)
- `frontend/src/utils/storage.js`

**What to Add:**

### JWT Token Storage
```javascript
// utils/storage.js

export const TokenStorage = {
  // Save JWT token
  saveToken(token) {
    localStorage.setItem('jwt_token', token);
    // Also set expiration
    const decoded = this.decodeToken(token);
    localStorage.setItem('token_expires', decoded.exp);
  },

  // Get JWT token
  getToken() {
    const token = localStorage.getItem('jwt_token');
    if (!token) return null;

    // Check if expired
    const expires = localStorage.getItem('token_expires');
    if (expires && Date.now() / 1000 > parseInt(expires)) {
      this.clearToken();
      return null;
    }

    return token;
  },

  // Clear token (logout)
  clearToken() {
    localStorage.removeItem('jwt_token');
    localStorage.removeItem('token_expires');
  },

  // Decode token (without verification)
  decodeToken(token) {
    try {
      const payload = token.split('.')[1];
      return JSON.parse(atob(payload));
    } catch (e) {
      return null;
    }
  }
};
```

---

## ✅ Task 2: Update Login Component

**File:** `frontend/src/components/Login.jsx` (or equivalent)

**What to Change:**

### Handle Login Response
```javascript
const handleLogin = async (email, password) => {
  try {
    const response = await fetch('http://localhost:13390/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    const data = await response.json();

    if (data.success) {
      // Save JWT token
      TokenStorage.saveToken(data.user.jwt_token);

      // Update auth context
      setUser({
        id: data.user.user_id,
        email: data.user.email,
        name: data.user.name,
        accountType: data.user.account_type
      });

      // Redirect to dashboard
      navigate('/dashboard');
    } else {
      setError(data.message || 'Login failed');
    }
  } catch (error) {
    setError('Network error. Please try again.');
  }
};
```

---

## ✅ Task 3: Update API Client with JWT

**File:** `frontend/src/api/client.js` (or equivalent)

**What to Add:**

### Automatic JWT Header Injection
```javascript
// api/client.js

import { TokenStorage } from '../utils/storage';

export class APIClient {
  constructor(baseURL = 'http://localhost:13390') {
    this.baseURL = baseURL;
  }

  // Make authenticated request
  async request(endpoint, options = {}) {
    const token = TokenStorage.getToken();

    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    };

    // Add JWT token if available
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers
    });

    // Handle 401 (token expired)
    if (response.status === 401) {
      TokenStorage.clearToken();
      window.location.href = '/login';
      throw new Error('Session expired');
    }

    return response.json();
  }

  // Convenience methods
  async get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  }

  async post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }
}

export const api = new APIClient();
```

---

## ✅ Task 4: Add Logout Functionality

**File:** `frontend/src/components/Navbar.jsx` (or equivalent)

**What to Add:**

### Logout Button Handler
```javascript
const handleLogout = async () => {
  try {
    // Call logout endpoint (optional, JWT is stateless)
    await fetch('http://localhost:13390/auth/logout', {
      method: 'POST'
    });
  } catch (error) {
    console.log('Logout endpoint not responding');
  } finally {
    // Clear local storage
    TokenStorage.clearToken();

    // Clear auth context
    setUser(null);

    // Redirect to login
    navigate('/login');
  }
};
```

---

## ✅ Task 5: Add Protected Route Component

**File:** `frontend/src/components/ProtectedRoute.jsx`

**Create New Component:**

```javascript
import { Navigate } from 'react-router-dom';
import { TokenStorage } from '../utils/storage';

export const ProtectedRoute = ({ children }) => {
  const token = TokenStorage.getToken();

  if (!token) {
    // Redirect to login if no token
    return <Navigate to="/login" replace />;
  }

  // Token exists, render children
  return children;
};

// Usage in routes
<Route path="/dashboard" element={
  <ProtectedRoute>
    <Dashboard />
  </ProtectedRoute>
} />
```

---

## ✅ Task 6: Add Frontend Tests

**File:** `frontend/tests/auth.test.js`

**Create Tests:**

```javascript
import { describe, it, expect, beforeEach } from 'vitest';
import { TokenStorage } from '../src/utils/storage';

describe('TokenStorage', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('should save and retrieve token', () => {
    const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...';
    TokenStorage.saveToken(token);

    const retrieved = TokenStorage.getToken();
    expect(retrieved).toBe(token);
  });

  it('should return null for expired token', () => {
    // Create expired token
    const expiredToken = 'expired.token.here';
    localStorage.setItem('jwt_token', expiredToken);
    localStorage.setItem('token_expires', '1000000000'); // Past date

    const retrieved = TokenStorage.getToken();
    expect(retrieved).toBeNull();
  });

  it('should clear token on logout', () => {
    TokenStorage.saveToken('test.token.here');
    TokenStorage.clearToken();

    expect(localStorage.getItem('jwt_token')).toBeNull();
    expect(localStorage.getItem('token_expires')).toBeNull();
  });
});
```

---

## 📊 Deliverables Checklist

When done, report back with:

- [ ] JWT token storage implemented
- [ ] Login component updated
- [ ] API client with JWT headers
- [ ] Logout functionality added
- [ ] Protected routes working
- [ ] Frontend tests passing

---

## ⚠️ Important Guidelines

### **Do NOT Modify:**
- ❌ Any files in `server/` directory
- ❌ Any files in `tests/` directory (backend tests)
- ❌ Any files in `specs/` or `docs/`
- ❌ Backend code

### **Only Modify:**
- ✅ Files in `frontend/` directory
- ✅ Files in `ui/` directory
- ✅ Files in `web/` directory
- ✅ Frontend tests only

### **Collaboration Safety:**
- ✅ Your work is in different directories than others
- ✅ No code conflicts with backend work
- ✅ Can commit independently
- ✅ Frontend-only changes

---

## 🚀 Getting Started (When You Return)

```bash
# 1. Pull latest changes
git pull

# 2. Create branch
git checkout -b feature/jwt-frontend-integration

# 3. Install dependencies if needed
cd frontend
npm install

# 4. Do your work (files listed above)

# 5. Test locally
npm run dev
# Test login at http://localhost:3000

# 6. Run tests
npm test

# 7. Commit
git add frontend/
git commit -m "feat: Add JWT authentication to frontend"

# 8. Push
git push origin feature/jwt-frontend-integration
```

---

## 🧪 Testing Your Changes

### Manual Testing:
1. Start backend: `make apple-dev-up` (or existing running API)
2. Start frontend: `cd frontend && npm run dev`
3. Test signup: Create new account
4. Test login: Login with credentials
5. Check token: Open DevTools → localStorage → jwt_token
6. Test protected route: Navigate to dashboard
7. Test logout: Click logout, verify redirect
8. Test expired token: Manually expire token, verify redirect

### Automated Testing:
```bash
cd frontend
npm test
```

---

## 📚 Reference Documentation

**Already Created:**
- `/docs/JWT_TOKEN_USAGE.md` - Backend JWT guide
- `/docs/SIGNUP_FIX_COMPLETE.md` - Implementation details
- `/docs/SESSION_COMPLETE_SUMMARY.md` - What's been done

**API Endpoints:**
- POST `/auth/signup/individual` - Create account
- POST `/auth/login` - Get JWT token
- POST `/auth/logout` - Clear session (optional)
- GET `/memory/list` - Test authenticated endpoint

---

## ❓ Questions?

**If stuck:**
1. Check backend docs for API contract
2. Test API endpoints with curl first
3. Inspect JWT token in jwt.io
4. Ask for clarification

**Estimated time:** 4-6 hours
**Difficulty:** Medium (frontend integration)
**Risk:** Medium (frontend files only, no backend conflicts)

---

**Come back when ready! We'll be waiting. 👋**
