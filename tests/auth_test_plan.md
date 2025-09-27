# 🧪 Auth API Test Plan - Comprehensive Edge Cases

## Overview
This test plan covers all authentication endpoints with focus on edge cases, error handling, and security validation.

## Test Environment Setup
```bash
# 1. Start the stack
make nina-stack-up

# 2. Verify endpoints are available
curl http://localhost:13370/health
curl http://localhost:13370/docs

# 3. Check auth routes are registered
curl http://localhost:13370/openapi.json | jq '.paths | keys | .[] | select(contains("auth"))'
```

## 🔐 Login Endpoint Tests (`POST /auth/login`)

### ✅ Valid Cases
| Test Case | Input | Expected Output | Status Code |
|-----------|-------|-----------------|-------------|
| Valid individual user | `{"email": "user@example.com", "password": "validpass123"}` | JWT token + user info | 200 |
| Valid org admin | `{"email": "admin@company.com", "password": "adminpass123"}` | JWT token + org info | 200 |
| Case insensitive email | `{"email": "USER@EXAMPLE.COM", "password": "validpass123"}` | JWT token | 200 |

### ❌ Error Cases
| Test Case | Input | Expected Error | Status Code |
|-----------|-------|----------------|-------------|
| Missing email | `{"password": "test123"}` | "Email and password are required" | 400 |
| Missing password | `{"email": "test@example.com"}` | "Email and password are required" | 400 |
| Empty email | `{"email": "", "password": "test123"}` | "Email and password are required" | 400 |
| Empty password | `{"email": "test@example.com", "password": ""}` | "Email and password are required" | 400 |
| Invalid email format | `{"email": "not-an-email", "password": "test123"}` | "Invalid email format" | 400 |
| Non-existent user | `{"email": "fake@example.com", "password": "test123"}` | "Invalid email or password" | 401 |
| Wrong password | `{"email": "real@example.com", "password": "wrongpass"}` | "Invalid email or password" | 401 |
| Unverified email | `{"email": "unverified@example.com", "password": "test123"}` | "Email verification required" | 403 |

### 🔒 Security Edge Cases
| Test Case | Input | Expected Behavior | Notes |
|-----------|-------|-------------------|-------|
| SQL injection attempt | `{"email": "'; DROP TABLE users; --", "password": "test"}` | Safe error handling | Should not crash |
| XSS attempt | `{"email": "<script>alert('xss')</script>", "password": "test"}` | Sanitized response | No script execution |
| Very long email | `{"email": "a" * 1000 + "@example.com", "password": "test"}` | Validation error | Input length limits |
| Unicode characters | `{"email": "tëst@éxample.com", "password": "tëst123"}` | Proper handling | Unicode support |
| Rate limiting | Multiple rapid requests | Rate limit response | After N attempts |

## 📝 Individual Signup Tests (`POST /auth/signup/individual`)

### ✅ Valid Cases
| Test Case | Input | Expected Output | Status Code |
|-----------|-------|-----------------|-------------|
| Valid signup | `{"email": "new@example.com", "password": "strongpass123", "full_name": "John Doe"}` | User created + verification email | 201 |
| Minimum valid password | `{"email": "test@example.com", "password": "12345678", "full_name": "Test"}` | User created | 201 |

### ❌ Error Cases
| Test Case | Input | Expected Error | Status Code |
|-----------|-------|----------------|-------------|
| Duplicate email | Existing email | "Email already registered" | 409 |
| Weak password | `{"password": "123"}` | "Password must be at least 8 characters" | 400 |
| Invalid email | `{"email": "invalid"}` | "Invalid email format" | 400 |
| Missing required fields | Missing email/password/name | Validation error | 422 |

### 🔒 Security Edge Cases
| Test Case | Input | Expected Behavior | Notes |
|-----------|-------|-------------------|-------|
| Password with special chars | `{"password": "P@ssw0rd!#$"}` | Accepted | Should support special chars |
| Very long password | `{"password": "a" * 200}` | Handled gracefully | Length limits |
| Empty name | `{"full_name": ""}` | Validation error | Required field |
| HTML in name | `{"full_name": "<b>John</b>"}` | Sanitized | No HTML execution |

## 🏢 Organization Signup Tests (`POST /auth/signup/organization`)

### ✅ Valid Cases
| Test Case | Input | Expected Output | Status Code |
|-----------|-------|-----------------|-------------|
| Valid org signup | Complete org data | Org + admin user created | 201 |
| Minimum required fields | Essential fields only | Org created | 201 |

### ❌ Error Cases
| Test Case | Input | Expected Error | Status Code |
|-----------|-------|----------------|-------------|
| Duplicate org name | Existing org name | "Organization name taken" | 409 |
| Invalid admin email | Invalid email format | "Invalid email format" | 400 |
| Missing org name | No organization name | Validation error | 422 |

## 🔧 Additional Auth Endpoints

### Email Verification (`POST /auth/verify-email`)
- Valid token verification
- Expired token handling
- Invalid token format
- Already verified user

### Password Reset (if implemented)
- Valid email reset request
- Non-existent email handling
- Token expiration
- Token reuse prevention

## 🚀 Performance Tests

### Load Testing
```bash
# Test concurrent logins
for i in {1..10}; do
  curl -X POST http://localhost:13370/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"test123"}' &
done
wait
```

### Response Time Requirements
- Login: < 500ms
- Signup: < 1000ms
- Error responses: < 200ms

## 🔍 JWT Token Validation

### Token Structure Tests
- Valid JWT format
- Correct algorithm (HS256)
- Required claims present
- Expiration time set
- Token signature validation

### Token Usage Tests
- Bearer token in Authorization header
- Token expiration handling
- Invalid token format
- Malformed token
- Expired token usage

## 🛡️ Security Checklist

### Authentication Security
- [ ] Passwords are hashed (bcrypt/argon2)
- [ ] No passwords in logs
- [ ] Rate limiting on auth endpoints
- [ ] Account lockout after failed attempts
- [ ] Secure JWT secret
- [ ] HTTPS in production

### Input Validation
- [ ] Email format validation
- [ ] Password strength requirements
- [ ] SQL injection prevention
- [ ] XSS prevention
- [ ] Input length limits
- [ ] Unicode handling

### Error Handling
- [ ] No sensitive data in error messages
- [ ] Consistent error format
- [ ] Proper HTTP status codes
- [ ] Logging of security events
- [ ] Graceful failure handling

## 📊 Test Execution Commands

```bash
# Run all auth tests
pytest tests/auth/ -v

# Run specific test categories
pytest tests/auth/test_login.py -v
pytest tests/auth/test_signup.py -v
pytest tests/auth/test_security.py -v

# Run with coverage
pytest tests/auth/ --cov=server/signup_api --cov-report=html

# Performance testing
pytest tests/auth/test_performance.py --benchmark-only
```

## 🎯 Success Criteria

### Functional Requirements
- ✅ All valid cases return expected results
- ✅ All error cases return appropriate errors
- ✅ JWT tokens are properly formatted and signed
- ✅ Email verification flow works end-to-end

### Security Requirements
- ✅ No security vulnerabilities in auth flow
- ✅ Proper input validation and sanitization
- ✅ Rate limiting prevents brute force attacks
- ✅ Sensitive data is properly protected

### Performance Requirements
- ✅ Response times meet requirements
- ✅ System handles concurrent requests
- ✅ No memory leaks under load
- ✅ Database queries are optimized

---

**Next Steps:**
1. Implement test cases using pytest
2. Create automated test scripts
3. Set up CI/CD pipeline for continuous testing
4. Monitor auth endpoints in production
