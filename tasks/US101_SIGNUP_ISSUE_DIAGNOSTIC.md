# US-101 Signup Page Disabled - Diagnostic Guide

**Issue:** Unable to type on signup page at http://localhost:8101/signup
**Impact:** Blocks manual QA for US-101
**Date:** October 26, 2025, 11:36 AM

---

## 🔍 Issue Analysis

### Code Review ✅
The signup code looks **correct**:
- **Signup.tsx** (lines 99-147): No `disabled` attributes on inputs
- **AuthLayout.tsx** (line 18): `pointer-events-none` only on background decorations (correct)
- Form structure is proper

### Possible Causes

#### 1. **Browser Console Errors** (Most Likely)
JavaScript errors can prevent React from rendering interactive elements.

**Check:**
1. Open browser DevTools (F12 or Cmd+Option+I)
2. Go to Console tab
3. Look for RED errors

**Common Issues:**
- API connection errors
- Missing environment variables
- React Router errors
- Module loading failures

---

## 🛠️ Troubleshooting Steps

### Step 1: Check Browser Console

```bash
# In browser at http://localhost:8101/signup
# Press F12 or Cmd+Option+I
# Look at Console tab

Expected: No red errors
If errors present: Screenshot and share
```

**Common Errors to Look For:**
- `Failed to fetch` → API not reachable
- `Cannot read property of undefined` → Missing config
- `Module not found` → Build issue
- `CORS error` → API configuration issue

---

### Step 2: Check Network Tab

```bash
# In DevTools, go to Network tab
# Refresh page (Cmd+R)
# Look for failed requests (red status codes)

Check:
- Are assets loading? (index.js, index.css)
- Are API calls working? (if any on page load)
- Any 404 or 500 errors?
```

---

### Step 3: Check Environment Variables

The customer UI needs to know where the API is:

```bash
# Check if environment is set in container
container exec ninaivalaigal-dev-ui-customer sh -c "env | grep -i api"

# Expected output should show API URL like:
# VITE_API_URL=http://192.168.66.163:13370
# or similar
```

**If Missing:** The UI doesn't know where to send requests!

---

### Step 4: Rebuild Customer UI

Container might have stale build:

```bash
# Stop customer UI
container stop ninaivalaigal-dev-ui-customer

# Remove container
container rm ninaivalaigal-dev-ui-customer

# Rebuild with no cache
cd /Users/swami/WorkSpace/ninaivalaigal/apps/customer
container build --no-cache -t ninaivalaigal-customer-ui:latest-docker .

# Restart the stack
make stack-start
```

---

### Step 5: Check API Connectivity

```bash
# From your terminal, check if API is reachable
curl -s http://192.168.66.163:13370/health

# If that fails, check localhost
curl -s http://localhost:13370/health

# Check auth endpoints specifically
curl -s http://localhost:13370/auth/health || echo "Auth endpoint not found"
```

---

### Step 6: Inspect Element

In browser:
1. Right-click on any input field
2. Select "Inspect Element"
3. Check the Styles panel for:
   - `pointer-events: none` (BAD - should not be on inputs)
   - `disabled` attribute (BAD - should not be present)
   - `opacity: 0` or `display: none` on parent (BAD)

---

## 🚨 Quick Fixes

### Fix 1: Hard Refresh
```bash
# In browser on signup page
Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)

# This clears cache and reloads everything
```

### Fix 2: Clear Browser Cache
```bash
# Chrome DevTools
1. Open DevTools (F12)
2. Right-click the reload button
3. Select "Empty Cache and Hard Reload"
```

### Fix 3: Try Different Browser
```bash
# If using Chrome, try Safari or Firefox
# This eliminates browser-specific issues
```

### Fix 4: Check for Overlays
```bash
# In browser console, run:
document.querySelectorAll('[style*="position: fixed"]')
document.querySelectorAll('[style*="position: absolute"]')

# Look for any elements covering the page
```

---

## 📋 Information to Collect

If still not working, collect this info:

### 1. Browser Console
```bash
# Screenshot all errors in Console tab
# Copy any error messages
```

### 2. Container Logs
```bash
container logs ninaivalaigal-dev-ui-customer | tail -50
container logs ninaivalaigal-dev-core-api | tail -50
```

### 3. Environment Check
```bash
# Check customer UI environment
container exec ninaivalaigal-dev-ui-customer env | grep VITE

# Check API is running
curl -I http://localhost:13370/health
```

### 4. Network Errors
```bash
# In DevTools Network tab
# Filter: "All"
# Look for red (failed) requests
# Screenshot the failed requests
```

---

## 🎯 Most Likely Issues (Ranked)

### 1. **JavaScript Error** (70% probability)
- Browser console has errors
- React can't mount properly
- **Fix:** Check console, fix errors

### 2. **Missing Environment Variables** (15% probability)
- UI doesn't know where API is
- **Fix:** Check VITE_API_URL is set

### 3. **Stale Build** (10% probability)
- Container has old code
- **Fix:** Rebuild with `--no-cache`

### 4. **API Connection Issue** (5% probability)
- UI can't reach API
- **Fix:** Verify API health and networking

---

## 📝 Report Template

```markdown
**Issue:** Signup page disabled

**Browser:** [Chrome/Safari/Firefox] [Version]

**Console Errors:**
[Paste screenshot or text]

**Network Errors:**
[List failed requests]

**Environment Check:**
[Paste output of env | grep VITE]

**Steps Tried:**
- [ ] Hard refresh (Cmd+Shift+R)
- [ ] Checked console
- [ ] Checked network tab
- [ ] Tried different browser
- [ ] Rebuilt container
```

---

## 🔧 Developer A Action Items

1. **Open browser DevTools** on http://localhost:8101/signup
2. **Check Console tab** for any red errors
3. **Check Network tab** for failed requests
4. **Report findings** using template above
5. **Try Quick Fixes** (hard refresh, different browser)

---

## 🚀 Once Fixed

After the issue is resolved:

```bash
# Test the full flow
1. Go to http://localhost:8101/signup
2. Fill in: Name, Email, Password
3. Click "Sign Up"
4. Verify:
   - No errors in console
   - Form submits successfully
   - Redirects to dashboard OR shows success message

# Document in US-101
- What the issue was
- How it was fixed
- Add to troubleshooting guide
```

---

**Priority:** URGENT - Blocks US-101 manual QA
**Next:** Developer A to run diagnostics and report findings
