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
  email: 'logout@example.com',
  name: 'Logout Tester',
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
    accessToken: 'logout-access-token',
    refreshToken: 'logout-refresh-token',
    accessExpires: now + 3600,
    refreshExpires: now + 7200,
  });
}

test.describe('Logout flows', () => {
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

  test('logs out an individual session and removes it from the list', async ({ page }) => {
    const sessions = [
      {
        id: 'session-current',
        created_at: '2025-10-11T09:00:00.000Z',
        last_active_at: '2025-10-12T09:45:00.000Z',
        ip_address: '192.0.2.1',
        is_current: true,
        location: 'Austin, USA',
        device: 'MacBook Pro',
      },
      {
        id: 'session-remote',
        created_at: '2025-10-10T11:15:00.000Z',
        last_active_at: '2025-10-12T11:47:00.000Z',
        ip_address: '198.51.100.20',
        is_current: false,
        location: 'Dallas, USA',
        device: 'Office PC',
      },
    ];

    await page.route('**/auth/sessions', async (route) => {
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sessions),
      });
    });

    await page.route('**/auth/sessions/session-remote', async (route) => {
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ success: true }),
      });
    });

    await page.goto('/dashboard/sessions');
    await expect(page.getByText('Office PC')).toBeVisible();

    const logoutButton = page.getByTestId('logout-session-session-remote');
    await expect(logoutButton).toBeEnabled();
    await logoutButton.click();

    await expect(page.getByText('Session logged out successfully.')).toBeVisible();
    await expect(page.locator('text=Office PC')).toHaveCount(0);
  });

  test('logs out all devices, redirects to login, and clears stored tokens', async ({ page }) => {
    await page.route('**/auth/sessions', async (route) => {
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify([
          {
            id: 'session-current',
            created_at: '2025-10-11T09:00:00.000Z',
            last_active_at: '2025-10-12T09:45:00.000Z',
            ip_address: '192.0.2.1',
            is_current: true,
            location: 'Austin, USA',
            device: 'MacBook Pro',
          },
          {
            id: 'session-remote',
            created_at: '2025-10-10T11:15:00.000Z',
            last_active_at: '2025-10-12T11:47:00.000Z',
            ip_address: '198.51.100.20',
            is_current: false,
            location: 'Dallas, USA',
            device: 'Office PC',
          },
        ]),
      });
    });

    await page.route('**/auth/logout-all', async (route) => {
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ success: true }),
      });
    });

    await page.goto('/dashboard/sessions');

    await page.getByRole('button', { name: 'Logout all devices' }).click();
    await expect(page).toHaveURL(/\/login$/);

    const stored = await page.evaluate(() => ({
      access: window.localStorage.getItem('auth_access_token'),
      refresh: window.localStorage.getItem('auth_refresh_token'),
    }));
    expect(stored.access).toBeNull();
    expect(stored.refresh).toBeNull();
  });
});
