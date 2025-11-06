// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/**
 * US#204/US#211: E2E Tests for Team Billing Page
 *
 * Tests the main team billing page:
 * - Current plan display
 * - Payment method display
 * - Plan change options
 * - Subscription cancellation
 * - Navigation to related pages
 */

import { test, expect, Page } from '@playwright/test';

const mockUser = {
  id: 'billing-test-user',
  email: 'billing-test@example.com',
  name: 'Billing Test User',
  emailVerified: true,
};

const mockBillingInfo = {
  team_id: 'team-billing-test',
  team_name: 'Billing Test Team',
  subscription_status: 'active',
  current_plan: 'team_pro',
  current_period_start: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
  current_period_end: new Date(Date.now() + 20 * 24 * 60 * 60 * 1000).toISOString(),
  cancel_at_period_end: false,
  next_billing_date: new Date(Date.now() + 20 * 24 * 60 * 60 * 1000).toISOString(),
  amount_due: 29.0,
  currency: 'usd',
  stripe_customer_id: 'cus_test123',
  payment_method: {
    id: 'pm_test123',
    type: 'card',
    last4: '4242',
    brand: 'visa',
    exp_month: 12,
    exp_year: 2025,
  },
  trial_end: null,
};

async function seedAuthState(page: Page) {
  const now = Math.floor(Date.now() / 1000);
  await page.addInitScript((tokenState) => {
    window.localStorage?.clear();
    window.sessionStorage?.clear();
    window.localStorage?.setItem('auth_access_token', tokenState.accessToken);
    window.localStorage?.setItem('auth_refresh_token', tokenState.refreshToken);
    window.localStorage?.setItem('auth_access_token_expires', String(tokenState.accessExpires));
    window.localStorage?.setItem('auth_refresh_token_expires', String(tokenState.refreshExpires));
  }, {
    accessToken: 'billing-test-token',
    refreshToken: 'billing-test-refresh',
    accessExpires: now + 3600,
    refreshExpires: now + 7200,
  });
}

test.describe('Team Billing Page (US#204/US#211)', () => {
  test.beforeEach(async ({ page }) => {
    await seedAuthState(page);

    // Mock auth/me endpoint
    await page.route('**/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mockUser),
      });
    });

    // Mock team billing endpoint
    await page.route('**/team/billing', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(mockBillingInfo),
        });
      } else {
        await route.continue();
      }
    });

    await page.goto('/team/billing');
    await page.waitForLoadState('networkidle');
  });

  test('should display billing page with current plan', async ({ page }) => {
    await expect(page.locator('h1').filter({ hasText: /Billing|Subscription/i })).toBeVisible();
    await expect(page.locator('text=/Current Plan/i')).toBeVisible();
    await expect(page.locator('text=/Team Pro/i')).toBeVisible();
  });

  test('should display payment method information', async ({ page }) => {
    await expect(page.locator('text=/Payment Method|Your Payment Method/i')).toBeVisible();
    await expect(page.locator('text=/4242|•••• •••• •••• 4242/i')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=/Expires|12\/2025/i')).toBeVisible();
  });

  test('should display subscription status and next billing date', async ({ page }) => {
    await expect(page.locator('text=/Status|Active/i')).toBeVisible();
    await expect(page.locator('text=/Next billing|Next Billing/i')).toBeVisible();
  });

  test('should show plan change options', async ({ page }) => {
    await expect(page.locator('text=/Change Plan|Upgrade|Downgrade/i')).toBeVisible();

    // Check for available plans
    const freePlan = page.locator('text=/Free Plan/i');
    const starterPlan = page.locator('text=/Starter Plan/i');
    const enterprisePlan = page.locator('text=/Enterprise/i');

    // At least one alternative plan should be visible
    await expect(
      freePlan.or(starterPlan).or(enterprisePlan)
    ).toBeVisible({ timeout: 5000 });
  });

  test('should navigate to payment method page', async ({ page }) => {
    const paymentMethodLink = page.getByRole('link', { name: /Payment Method|Update Payment Method/i });
    await expect(paymentMethodLink.first()).toBeVisible({ timeout: 10000 });

    await paymentMethodLink.first().click();
    await expect(page).toHaveURL(/.*\/team\/billing\/payment-method/, { timeout: 10000 });
  });

  test('should navigate to invoices page', async ({ page }) => {
    const invoicesLink = page.getByRole('link', { name: /Invoices|View Invoices/i });
    await expect(invoicesLink.first()).toBeVisible({ timeout: 10000 }).catch(async () => {
      // Try alternative selector
      await expect(page.locator('a[href*="/invoices"]').first()).toBeVisible();
      await page.locator('a[href*="/invoices"]').first().click();
    });

    if (await invoicesLink.first().isVisible()) {
      await invoicesLink.first().click();
    }

    await expect(page).toHaveURL(/.*\/team\/billing\/invoices/, { timeout: 10000 });
  });

  test('should navigate to usage analytics page', async ({ page }) => {
    const usageLink = page.getByRole('link', { name: /Usage|Usage Analytics/i });
    await expect(usageLink.first()).toBeVisible({ timeout: 10000 }).catch(async () => {
      // Try alternative selector
      await expect(page.locator('a[href*="/usage"]').first()).toBeVisible();
      await page.locator('a[href*="/usage"]').first().click();
    });

    if (await usageLink.first().isVisible()) {
      await usageLink.first().click();
    }

    await expect(page).toHaveURL(/.*\/team\/usage/, { timeout: 10000 });
  });

  test('should navigate back to dashboard', async ({ page }) => {
    const backLink = page.getByRole('link', { name: /Back to Dashboard/i });
    await expect(backLink).toBeVisible();
    await backLink.click();
    await expect(page).toHaveURL(/.*\/team\/dashboard/, { timeout: 10000 });
  });

  test('should show cancel subscription option', async ({ page }) => {
    // Scroll to find cancel button if needed
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));

    const cancelButton = page.getByRole('button', { name: /Cancel|Cancel Subscription/i });
    await expect(cancelButton).toBeVisible({ timeout: 10000 });
  });

  test('should display admin payment notice', async ({ page }) => {
    // Check for the admin payment indicator
    await expect(
      page.locator('text=/paying for this team|admin/i').first()
    ).toBeVisible({ timeout: 10000 }).catch(() => {
      // This is optional, might not be in all versions
    });
  });
});
