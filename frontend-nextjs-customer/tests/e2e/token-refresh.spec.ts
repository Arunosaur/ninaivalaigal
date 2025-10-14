// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { test, expect, Page } from '@playwright/test';

const mockUser = {
  id: 'user-1',
  email: 'refresh@example.com',
  name: 'Refresh Tester',
};

function futureEpoch(minutes: number) {
  return Math.floor(Date.now() / 1000) + minutes * 60;
}

async function seedAuthState(page: Page, overrides?: Partial<{
  accessToken: string;
  refreshToken: string;
  accessExpires: number;
  refreshExpires: number;
}>) {
  const state = {
    accessToken: 'stale-access-token',
    refreshToken: 'valid-refresh-token',
    accessExpires: futureEpoch(10),
    refreshExpires: futureEpoch(60),
    ...overrides,
  };

  await page.addInitScript((tokenState) => {
    window.localStorage?.clear();
    window.sessionStorage?.clear();
    window.localStorage?.setItem('auth_access_token', tokenState.accessToken);
    window.localStorage?.setItem('auth_refresh_token', tokenState.refreshToken);
    window.localStorage?.setItem('auth_access_token_expires', String(tokenState.accessExpires));
    window.localStorage?.setItem('auth_refresh_token_expires', String(tokenState.refreshExpires));
  }, state);
}

test.describe('Token refresh handling', () => {
  test.beforeEach(async ({ page }) => {
    await seedAuthState(page);

    await page.route('**/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mockUser),
      });
    });
  });

  test('automatically refreshes access token when an API call returns 401', async ({ page }) => {
    const sessionsPayload = [
      {
        id: 'session-desktop',
        created_at: '2025-10-12T10:00:00.000Z',
        last_active_at: '2025-10-12T10:15:00.000Z',
        ip_address: '203.0.113.30',
        is_current: true,
        location: 'Austin, USA',
        device: 'Office PC',
      },
    ];

    let sessionRequestCount = 0;
    await page.route('**/auth/sessions', async (route) => {
      sessionRequestCount += 1;
      if (sessionRequestCount === 1) {
        await route.fulfill({
          status: 401,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ detail: 'Access token expired' }),
        });
        return;
      }

      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sessionsPayload),
      });
    });

    let refreshRequestCount = 0;
    await page.route('**/auth/refresh', async (route) => {
      refreshRequestCount += 1;
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          access_token: 'fresh-access-token',
          token_type: 'bearer',
          expires_in: 3600,
          refresh_token: 'fresh-refresh-token',
          refresh_expires_in: 7200,
        }),
      });
    });

    await page.goto('/dashboard/sessions');

    await expect(page.getByText('Office PC')).toBeVisible();
    expect(refreshRequestCount).toBeGreaterThan(0);

    const stored = await page.evaluate(() => ({
      access: window.localStorage.getItem('auth_access_token'),
      refresh: window.localStorage.getItem('auth_refresh_token'),
    }));
    expect(stored.access).toBe('fresh-access-token');
    expect(stored.refresh).toBe('fresh-refresh-token');
  });

  test('surfaces an error when refresh fails with 401 and clears stored tokens', async ({ page }) => {
    await page.route('**/auth/sessions', async (route) => {
      await route.fulfill({
        status: 401,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ detail: 'Token expired' }),
      });
    });

    await page.route('**/auth/refresh', async (route) => {
      await route.fulfill({
        status: 401,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ detail: 'Refresh token invalid' }),
      });
    });

    await page.goto('/dashboard/sessions');

    await expect(page.getByText('Unable to load sessions')).toBeVisible();
    await expect(page.getByText('Your session has expired. Please sign in again.')).toBeVisible();
    await expect(page.getByText('Session refresh failed')).toBeVisible();

    const stored = await page.evaluate(() => ({
      access: window.localStorage.getItem('auth_access_token'),
      refresh: window.localStorage.getItem('auth_refresh_token'),
    }));
    expect(stored.access).toBeNull();
    expect(stored.refresh).toBeNull();
  });

  test('shows a retry prompt when refresh succeeds without returning a token', async ({ page }) => {
    await page.route('**/auth/sessions', async (route) => {
      await route.fulfill({
        status: 401,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ detail: 'Token expired' }),
      });
    });

    await page.route('**/auth/refresh', async (route) => {
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ success: true }),
      });
    });

    await page.goto('/dashboard/sessions');

    await expect(page.getByText('Session refresh failed')).toBeVisible();
    await expect(
      page.getByText('Unable to refresh your session: the server did not return a new token.'),
    ).toBeVisible();

    const stored = await page.evaluate(() => ({
      access: window.localStorage.getItem('auth_access_token'),
      refresh: window.localStorage.getItem('auth_refresh_token'),
    }));
    expect(stored.access).toBeNull();
    expect(stored.refresh).toBeNull();

    await expect(page.getByRole('button', { name: 'Retry now' })).toBeVisible();
  });
});
