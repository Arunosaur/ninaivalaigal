# Developer A - Task Assignment (CORRECTED PATHS)

**Date:** October 12, 2025 - 18:10 (Updated: 18:35)
**Status:** ✅ READY - Paths Corrected for Next.js Structure
**Focus:** Frontend JWT Integration in Next.js Customer App
**Risk Level:** ⚠️ MEDIUM (Frontend files only)

---

## 🎯 Your Mission

Integrate JWT authentication into the **Next.js Customer App** (`frontend-nextjs-customer/`)

**Working Directory:** `frontend-nextjs-customer/`
**No Backend Changes:** Frontend only
**Duration:** 4-6 hours

---

## 📂 Correct File Paths (Next.js Structure)

**Your workspace has:**
- ✅ `frontend-nextjs-customer/` - Main customer-facing app
- ✅ `frontend-nextjs-customer/contexts/AuthContext.tsx` - Already exists!
- ✅ `frontend-nextjs-customer/services/auth.service.ts` - Already exists!
- ✅ `frontend-nextjs-customer/utils/` - For token storage utilities

---

## ✅ Task 1: Add JWT Token Storage Utility

**File:** `frontend-nextjs-customer/utils/tokenStorage.ts` (CREATE NEW)

**Create new file:**

```typescript
// utils/tokenStorage.ts

export class TokenStorage {
  private static readonly TOKEN_KEY = 'jwt_token';
  private static readonly EXPIRY_KEY = 'token_expires';

  /**
   * Save JWT token to localStorage
   */
  static saveToken(token: string): void {
    if (typeof window === 'undefined') return; // SSR safety

    localStorage.setItem(this.TOKEN_KEY, token);

    // Decode and store expiration
    const payload = this.decodeToken(token);
    if (payload?.exp) {
      localStorage.setItem(this.EXPIRY_KEY, payload.exp.toString());
    }
  }

  /**
   * Get JWT token from localStorage
   * Returns null if expired or missing
   */
  static getToken(): string | null {
    if (typeof window === 'undefined') return null; // SSR safety

    const token = localStorage.getItem(this.TOKEN_KEY);
    if (!token) return null;

    // Check if expired
    const expires = localStorage.getItem(this.EXPIRY_KEY);
    if (expires && Date.now() / 1000 > parseInt(expires)) {
      this.clearToken();
      return null;
    }

    return token;
  }

  /**
   * Clear token on logout
   */
  static clearToken(): void {
    if (typeof window === 'undefined') return;

    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.EXPIRY_KEY);
  }

  /**
   * Decode JWT token (without verification)
   */
  private static decodeToken(token: string): any {
    try {
      const payload = token.split('.')[1];
      return JSON.parse(atob(payload));
    } catch {
      return null;
    }
  }

  /**
   * Check if token exists and is valid
   */
  static isAuthenticated(): boolean {
    return this.getToken() !== null;
  }
}
```

---

## ✅ Task 2: Update AuthContext

**File:** `frontend-nextjs-customer/contexts/AuthContext.tsx` (MODIFY)

**Add TokenStorage import and update methods:**

```typescript
// Add at top
import { TokenStorage } from '@/utils/tokenStorage';

// In AuthContext, update login method:
const login = async (email: string, password: string) => {
  try {
    setLoading(true);
    setError(null);

    const response = await fetch('http://localhost:13390/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Login failed');
    }

    if (data.success && data.user) {
      // Save JWT token
      TokenStorage.saveToken(data.user.jwt_token);

      // Update user state
      setUser({
        id: data.user.user_id,
        email: data.user.email,
        name: data.user.name,
        accountType: data.user.account_type,
      });

      return data;
    }

    throw new Error('Login failed');
  } catch (err) {
    const error = err as Error;
    setError(error.message);
    throw error;
  } finally {
    setLoading(false);
  }
};

// Update logout method:
const logout = async () => {
  try {
    // Call logout endpoint (optional)
    await fetch('http://localhost:13390/auth/logout', {
      method: 'POST',
    }).catch(() => {
      // Ignore errors
    });
  } finally {
    // Always clear local storage
    TokenStorage.clearToken();
    setUser(null);
  }
};

// Add restore session on mount:
useEffect(() => {
  const token = TokenStorage.getToken();
  if (token) {
    // Verify token with API
    fetch('http://localhost:13390/user/profile', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setUser(data.user);
        } else {
          TokenStorage.clearToken();
        }
      })
      .catch(() => {
        TokenStorage.clearToken();
      });
  }
}, []);
```

---

## ✅ Task 3: Update Auth Service

**File:** `frontend-nextjs-customer/services/auth.service.ts` (MODIFY)

**Add automatic JWT header injection:**

```typescript
// Add at top
import { TokenStorage } from '@/utils/tokenStorage';

// Create API client with automatic auth headers
class APIClient {
  private baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:13390';

  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = TokenStorage.getToken();

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    };

    // Add JWT token if available
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers,
    });

    // Handle 401 (token expired)
    if (response.status === 401) {
      TokenStorage.clearToken();
      window.location.href = '/login';
      throw new Error('Session expired');
    }

    const data = await response.json();
    return data;
  }

  // Convenience methods
  get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  post<T>(endpoint: string, body?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    });
  }
}

export const apiClient = new APIClient();

// Use apiClient for all API calls:
export const authService = {
  async login(email: string, password: string) {
    return apiClient.post('/auth/login', { email, password });
  },

  async signup(email: string, password: string, name: string) {
    return apiClient.post('/auth/signup/individual', { email, password, name });
  },

  async logout() {
    return apiClient.post('/auth/logout');
  },
};
```

---

## ✅ Task 4: Add Middleware Protection

**File:** `frontend-nextjs-customer/middleware.ts` (CREATE NEW)

**Create route protection:**

```typescript
// middleware.ts (at root of frontend-nextjs-customer/)

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // Check if JWT token exists
  const token = request.cookies.get('jwt_token')?.value;

  const isPublicPath = request.nextUrl.pathname === '/login' ||
                       request.nextUrl.pathname === '/signup';

  // Redirect to login if accessing protected route without token
  if (!token && !isPublicPath) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // Redirect to dashboard if accessing login/signup with valid token
  if (token && isPublicPath) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  return NextResponse.next();
}

// Protect these routes
export const config = {
  matcher: ['/dashboard/:path*', '/memories/:path*', '/settings/:path*', '/login', '/signup'],
};
```

---

## ✅ Task 5: Update Login Page

**File:** `frontend-nextjs-customer/app/login/page.tsx` (MODIFY)

**Use updated AuthContext:**

```typescript
'use client';

import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login, error, loading } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      await login(email, password);
      router.push('/dashboard');
    } catch (err) {
      // Error handled by AuthContext
      console.error('Login failed:', err);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center">
      <form onSubmit={handleSubmit} className="w-full max-w-md space-y-4">
        <h1 className="text-2xl font-bold">Login</h1>

        {error && (
          <div className="bg-red-50 text-red-600 p-3 rounded">
            {error}
          </div>
        )}

        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
          className="w-full px-4 py-2 border rounded"
          required
        />

        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          className="w-full px-4 py-2 border rounded"
          required
        />

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </form>
    </div>
  );
}
```

---

## ✅ Task 6: Add Environment Variables

**File:** `frontend-nextjs-customer/.env.local` (MODIFY)

**Add API URL:**

```bash
NEXT_PUBLIC_API_URL=http://localhost:13390
```

---

## 📊 Deliverables Checklist

- [ ] Create `utils/tokenStorage.ts`
- [ ] Update `contexts/AuthContext.tsx`
- [ ] Update `services/auth.service.ts`
- [ ] Create `middleware.ts`
- [ ] Update `app/login/page.tsx`
- [ ] Update `.env.local`
- [ ] Test login flow
- [ ] Test protected routes
- [ ] Test logout
- [ ] Test token expiration

---

## ⚠️ Important Guidelines

### **Do NOT Modify:**
- ❌ Any files in `server/` directory
- ❌ Any files in `tests/` directory
- ❌ Any files in `specs/` or `docs/`
- ❌ Backend code

### **Only Modify:**
- ✅ Files in `frontend-nextjs-customer/` directory ONLY
- ✅ No shared packages (unless you coordinate)

---

## 🚀 Getting Started

```bash
# 1. Pull latest changes
git pull

# 2. Create branch
git checkout -b feature/jwt-frontend-integration

# 3. Navigate to customer app
cd frontend-nextjs-customer

# 4. Install dependencies if needed
npm install

# 5. Start dev server
npm run dev

# 6. Test at http://localhost:3000
```

---

## 🧪 Testing Your Changes

### **Manual Testing:**
1. Start backend: `make apple-dev-up` (or existing running API)
2. Start frontend: `cd frontend-nextjs-customer && npm run dev`
3. **Test signup:** Create new account at `/signup`
4. **Test login:** Login at `/login`
5. **Check token:** Open DevTools → Application → Local Storage → jwt_token
6. **Test protected route:** Navigate to `/dashboard`
7. **Test logout:** Click logout, verify redirect
8. **Test expiration:** Manually expire token, verify redirect

### **Verification:**
```bash
# In browser console:
localStorage.getItem('jwt_token')  # Should show token after login
localStorage.getItem('token_expires')  # Should show expiration timestamp
```

---

## 📚 API Endpoints Reference

**Backend already has these working:**
- POST `/auth/signup/individual` - Create account (returns JWT)
- POST `/auth/login` - Login (returns JWT)
- POST `/auth/logout` - Logout (optional)
- GET `/user/profile` - Get user profile (requires JWT)
- GET `/memory/list` - List memories (requires JWT)

**Authentication Header:**
```
Authorization: Bearer YOUR_JWT_TOKEN_HERE
```

---

## ❓ Questions?

**If stuck:**
1. Check backend docs: `/docs/JWT_TOKEN_USAGE.md`
2. Test API with curl first
3. Inspect JWT token at jwt.io
4. Ask for clarification

**Estimated time:** 4-6 hours
**Difficulty:** Medium (Next.js integration)
**Risk:** Medium (frontend files only, no backend conflicts)

---

**Paths are now correct for your Next.js structure! 🎉**
