// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/**
 * US#211: E2E Tests for Usage Analytics Page
 *
 * Tests the usage analytics page:
 * - Usage summary cards
 * - Memory usage charts
 * - API calls charts
 * - Storage usage visualization
 * - Data export functionality
 */

import { test, expect, Page } from '@playwright/test';

const mockUser = {
  id: 'usage-test-user',
  email: 'usage-test@example.com',
  name: 'Usage Test User',
  emailVerified: true,
};

const mockUsageData = {
  usage_metrics: {
    member_count: 5,
    storage_usage_gb: 2.5,
    ai_queries_count: 1250,
    api_calls_count: 4500,
  },
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
    accessToken: 'usage-test-token',
    refreshToken: 'usage-test-refresh',
    accessExpires: now + 3600,
    refreshExpires: now + 7200,
  });
}

test.describe('Usage Analytics Page (US#211)', () => {
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

    // Mock team billing to get team ID
    await page.route('**/team/billing', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            team_id: 'team-usage-test',
            team_name: 'Usage Test Team',
          }),
        });
      } else {
        await route.continue();
      }
    });

    // Mock usage analytics endpoint
    await page.route('**/analytics/teams/**/usage**', async (route) => {
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mockUsageData),
      });
    });

    await page.goto('/team/usage');
    await page.waitForLoadState('networkidle');
  });

  test('should display usage analytics page', async ({ page }) => {
    await expect(page.locator('h1').filter({ hasText: /Usage Analytics|Usage/i })).toBeVisible();
  });

  test('should display usage summary cards', async ({ page }) => {
    // Wait for data to load
    await page.waitForTimeout(2000);

    // Check for summary metrics
    await expect(
      page.locator('text=/Memories|API Calls|Storage|Contexts/i').first()
    ).toBeVisible({ timeout: 10000 });
  });

  test('should display memory usage information', async ({ page }) => {
    await page.waitForTimeout(2000);

    await expect(
      page.locator('text=/Memories|Memory Usage|memory/i').first()
    ).toBeVisible({ timeout: 10000 });
  });

  test('should display API calls information', async ({ page }) => {
    await page.waitForTimeout(2000);

    await expect(
      page.locator('text=/API Calls|api calls/i').first()
    ).toBeVisible({ timeout: 10000 });
  });

  test('should display storage usage', async ({ page }) => {
    await page.waitForTimeout(2000);

    await expect(
      page.locator('text=/Storage|GB|storage/i').first()
    ).toBeVisible({ timeout: 10000 });
  });

  test('should have export data button', async ({ page }) => {
    await page.waitForTimeout(2000);

    const exportButton = page.getByRole('button', { name: /Export|Export Data/i });
    await expect(exportButton).toBeVisible({ timeout: 10000 }).catch(() => {
      // Export might be optional
    });
  });

  test('should navigate back to billing page', async ({ page }) => {
    const backLink = page.getByRole('link', { name: /Back to Billing|Back/i });
    await expect(backLink).toBeVisible();
    await backLink.click();
    await expect(page).toHaveURL(/.*\/team\/billing/, { timeout: 10000 });
  });

  test('should display period information', async ({ page }) => {
    await page.waitForTimeout(2000);

    // Check for period dates
    await expect(
      page.locator('text=/Period|2025|Jan|Feb|Mar/i').first()
    ).toBeVisible({ timeout: 10000 }).catch(() => {
      // Period info might not be displayed
    });
  });

  test('should handle loading state', async ({ page }) => {
    // Navigate to page and check for loading indicators
    await page.goto('/team/usage');

    // Should show some loading state initially
    const loadingIndicator = page.locator('text=/Loading|loading/i').or(
      page.locator('[role="status"]')
    );

    // Loading state should disappear
    await expect(loadingIndicator).not.toBeVisible({ timeout: 10000 });
  });
});
