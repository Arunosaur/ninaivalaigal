# Stripe Integration Setup

## Getting Started with Stripe Elements (Test Mode)

### Step 1: Create Free Stripe Account
1. Go to [https://stripe.com](https://stripe.com)
2. Click "Start now" or "Sign up"
3. Create a free account (no credit card required)
4. Verify your email

### Step 2: Get Test Mode API Keys
1. Once logged in, go to **Developers** → **API keys**
2. You'll see two keys:
   - **Publishable key** (starts with `pk_test_...`)
   - **Secret key** (starts with `sk_test_...`)

### Step 3: Configure Environment Variables

#### Frontend (`.env.local`):
```bash
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_PUBLISHABLE_KEY_HERE
NEXT_PUBLIC_API_URL=http://localhost:13370
```

#### Backend (`.env` or `configs/defaults.env`):
```bash
STRIPE_SECRET_KEY=sk_test_YOUR_SECRET_KEY_HERE
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET_HERE  # Optional for now
```

### Step 4: Test Mode Benefits
✅ **Free** - No charges for test transactions  
✅ **Safe** - Test cards don't charge real money  
✅ **Full Features** - All Stripe features work in test mode  
✅ **Real Testing** - Test webhooks, subscriptions, invoices, etc.

### Test Card Numbers
Stripe provides test card numbers that work in test mode:

**Successful Payment:**
- Card: `4242 4242 4242 4242`
- Expiry: Any future date (e.g., `12/25`)
- CVC: Any 3 digits (e.g., `123`)
- ZIP: Any 5 digits (e.g., `12345`)

**Failed Payment:**
- Card: `4000 0000 0000 0002`

**Requires Authentication:**
- Card: `4000 0027 6000 3184`

### Security Notes
- ✅ Publishable keys can be safely exposed in frontend code
- ✅ Secret keys MUST be kept server-side only
- ✅ Test mode keys only work with test cards
- ✅ No real money is charged in test mode

### Moving to Production
When ready for production:
1. Toggle to "Live mode" in Stripe dashboard
2. Get live mode API keys
3. Update environment variables
4. Use real payment cards (will charge real money)

### Resources
- [Stripe Test Cards](https://stripe.com/docs/testing)
- [Stripe Elements Docs](https://stripe.com/docs/stripe-js)
- [Stripe React Components](https://stripe.com/docs/stripe-js/react)

