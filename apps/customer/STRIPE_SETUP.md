# Stripe Setup Guide

This document explains how to set up Stripe for payment method management in the customer app.

## Quick Start

1. **Create a Stripe Account** (if you don't have one)
   - Go to: https://dashboard.stripe.com/register
   - Complete the account setup

2. **Get Your Publishable Key**
   - Log in to: https://dashboard.stripe.com/apikeys
   - Copy your **Test mode** publishable key (starts with `pk_test_`)
   - Or copy your **Live mode** publishable key (starts with `pk_live_`)

3. **Add Key to Environment**
   - Copy `.env.example` to `.env` (if it doesn't exist)
   - Add your key:
     ```bash
     VITE_STRIPE_PUBLISHABLE_KEY=pk_test_your_key_here
     ```
   - **Note:** Use `VITE_` prefix (not `NEXT_PUBLIC_`) - this is Vite, not Next.js!

4. **Restart Dev Server**
   ```bash
   npm run dev
   ```

## Testing Payment Methods

### Test Card Numbers

Stripe provides test card numbers for testing:

- **Success:** `4242 4242 4242 4242`
- **Decline:** `4000 0000 0000 0002`
- **3D Secure:** `4000 0025 0000 3155`

**Expiry:** Any future date (e.g., `12/25`)
**CVC:** Any 3 digits (e.g., `123`)
**ZIP:** Any 5 digits (e.g., `12345`)

### Where to Test

1. Navigate to: `/team/billing`
2. Click: **"Add Payment Method"** or **"Update Payment Method"**
3. Enter test card details
4. Submit the form

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_STRIPE_PUBLISHABLE_KEY` | Stripe publishable key | `pk_test_51AbC...` |

**Important:**
- Must start with `VITE_` to be exposed to the browser
- Never commit `.env` file with real keys to git
- Use test keys for development
- Use live keys only in production

## Troubleshooting

### "Stripe Not Configured" Error

**Cause:** `VITE_STRIPE_PUBLISHABLE_KEY` not set in `.env`

**Fix:**
1. Create `.env` file in `apps/customer/`
2. Add: `VITE_STRIPE_PUBLISHABLE_KEY=pk_test_...`
3. Restart dev server

### "Invalid API Key" Error

**Cause:** Wrong key format or invalid key

**Fix:**
1. Verify key starts with `pk_test_` or `pk_live_`
2. Copy key directly from Stripe Dashboard
3. Ensure no extra spaces or characters

### Payment Method Not Saving

**Cause:** Backend not configured or API endpoint missing

**Fix:**
1. Verify backend has `/team/billing/payment-method` endpoint
2. Check backend logs for errors
3. Ensure Stripe secret key is set in backend

## Production Deployment

For production:

1. Get **Live mode** publishable key from Stripe Dashboard
2. Set `VITE_STRIPE_PUBLISHABLE_KEY` in production environment
3. Ensure backend uses **Live mode** secret key
4. Test with real card (use small amount first)

## Security Notes

- ✅ Publishable keys are safe to expose in frontend
- ❌ Never expose secret keys in frontend
- ✅ Stripe Elements handles PCI compliance
- ✅ Card data never touches our servers

## More Information

- Stripe Dashboard: https://dashboard.stripe.com/
- Stripe Docs: https://stripe.com/docs/stripe-js/react
- Test Cards: https://stripe.com/docs/testing
