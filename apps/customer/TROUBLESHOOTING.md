# Troubleshooting Guide

## React "Invalid Hook Call" Error

**Symptom:**
```
Warning: Invalid hook call. Hooks can only be called inside of the body of a function component.
TypeError: Cannot read properties of null (reading 'useState')
```

**Cause:** Multiple instances of React in the same app

**Fix:**
1. Clear Vite cache:
   ```bash
   rm -rf node_modules/.vite
   ```

2. Reinstall dependencies:
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

3. Restart dev server:
   ```bash
   npm run dev
   ```

The `vite.config.ts` already includes `dedupe: ['react', 'react-dom']` which should prevent this issue.

---

## Server Not Starting on Port 8101

**Check if port is in use:**
```bash
lsof -i :8101
```

**Kill process if needed:**
```bash
kill -9 <PID>
```

**Or use different port:**
Edit `vite.config.ts`:
```typescript
server: {
  port: 8102, // or any available port
}
```

---

## Stripe Elements Not Loading

**Symptom:** "Stripe Not Configured" warning

**Fix:**
1. Create `.env` file in `apps/customer/`
2. Add: `VITE_STRIPE_PUBLISHABLE_KEY=pk_test_...`
3. Restart dev server

See `STRIPE_SETUP.md` for details.

---

## TypeScript Errors

**Fix:**
```bash
npm run type-check
```

Common issues:
- Missing imports → Add imports to `App.tsx`
- Type mismatches → Check component props

---

## Build Errors

**Clear cache and rebuild:**
```bash
rm -rf node_modules/.vite dist
npm run build
```

---

## Still Having Issues?

1. Check browser console for specific errors
2. Verify `package.json` dependencies
3. Ensure single React instance (check `npm ls react react-dom`)
4. Restart dev server completely
