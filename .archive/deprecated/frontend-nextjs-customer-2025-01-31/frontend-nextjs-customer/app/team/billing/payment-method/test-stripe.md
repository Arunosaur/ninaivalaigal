# Testing Stripe Elements Integration

## Quick Test Guide

### 1. Start Development Server
```bash
cd frontend-nextjs-customer
npm run dev
```

### 2. Navigate to Payment Method Page
Open: http://localhost:3000/team/billing/payment-method

### 3. Test Card Numbers (Stripe Test Mode)

#### ✅ Successful Payment
- **Card:** `4242 4242 4242 4242`
- **Expiry:** Any future date (e.g., `12/25`)
- **CVC:** Any 3 digits (e.g., `123`)
- **ZIP:** Any 5 digits (e.g., `12345`)

#### ❌ Declined Card
- **Card:** `4000 0000 0000 0002`

#### 🔐 Requires Authentication
- **Card:** `4000 0027 6000 3184`
- This will trigger 3D Secure authentication

### 4. Expected Flow

1. **Page Loads:**
   - Stripe Elements card input appears
   - Form is ready for input

2. **Enter Test Card:**
   - Type card number: `4242 4242 4242 4242`
   - Enter future expiry date
   - Enter CVC
   - Enter ZIP code

3. **Submit Form:**
   - Click "Add Payment Method"
   - Stripe creates payment method token
   - Backend API call to `/team/billing/payment-method`
   - Success message appears

4. **Check Browser Console:**
   - Look for: "Payment method created: pm_test_..."
   - Look for: "Payment method saved to backend"

### 5. Troubleshooting

**Issue: "Stripe is not initialized"**
- Check `.env.local` has `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`
- Restart dev server after adding key
- Key should start with `pk_test_`

**Issue: Card input not showing**
- Check browser console for Stripe errors
- Verify publishable key is correct
- Check network tab for Stripe API calls

**Issue: "Failed to save payment method"**
- Check backend API is running
- Verify `/team/billing/payment-method` endpoint works
- Check backend logs for errors

### 6. Testing Checklist

- [ ] Stripe Elements card input displays
- [ ] Can type card number
- [ ] Form validates card number format
- [ ] Submit creates payment method
- [ ] Backend receives payment method ID
- [ ] Success message appears
- [ ] Redirects to billing page
- [ ] Payment method appears on billing page

### 7. Browser DevTools

**Console Logs to Check:**
```
Payment method created: pm_test_...
Payment method saved to backend: {...}
```

**Network Tab:**
- Stripe API calls (to `api.stripe.com`)
- Backend API call to `/team/billing/payment-method`

**Elements Tab:**
- Check for Stripe iframes
- Verify card element is mounted
