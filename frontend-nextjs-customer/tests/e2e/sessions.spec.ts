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
  email: 'sessions@example.com',
  name: 'Sessions Tester',
};

const defaultAuthState = {
  accessToken: 'test-access-token',
  refreshToken: 'test-refresh-token',
  accessExpires: Math.floor(Date.now() / 1000) + 3600,
  refreshExpires: Math.floor(Date.now() / 1000) + 7200,
};

async function seedAuthState(page: Page, state = defaultAuthState) {
  await page.addInitScript((tokenState) => {
    window.localStorage?.clear();
    window.sessionStorage?.clear();
    window.localStorage?.setItem('auth_access_token', tokenState.accessToken);
    window.localStorage?.setItem('auth_refresh_token', tokenState.refreshToken);
    window.localStorage?.setItem('auth_access_token_expires', String(tokenState.accessExpires));
    window.localStorage?.setItem('auth_refresh_token_expires', String(tokenState.refreshExpires));
  }, state);
}

test.describe('Sessions management', () => {
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

  test('renders active sessions list with device metadata', async ({ page }) => {
    const mockSessions = [
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
        id: 'session-tablet',
        created_at: '2025-10-10T11:15:00.000Z',
        last_active_at: null,
        ip_address: '198.51.100.20',
        is_current: false,
        location: 'Dallas, USA',
        device: 'iPad Air',
      },
    ];

    await page.route('**/auth/sessions', async (route) => {
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mockSessions),
      });
    });

    await page.goto('/dashboard/sessions');

    await expect(page.getByRole('heading', { name: 'Active Sessions' })).toBeVisible();
    await expect(page.getByText('MacBook Pro')).toBeVisible();
    await expect(page.getByText('Current device')).toBeVisible();
    await expect(page.getByText('Austin, USA')).toBeVisible();
    await expect(page.getByText('192.0.2.1')).toBeVisible();
    await expect(page.getByText('iPad Air')).toBeVisible();
    await expect(page.getByText('Last active time unavailable')).toBeVisible();
  });

  test('shows empty state when there are no sessions', async ({ page }) => {
    await page.route('**/auth/sessions', async (route) => {
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify([]),
      });
    });

    await page.goto('/dashboard/sessions');

    await expect(page.getByText('No active sessions')).toBeVisible();
    await expect(page.getByText('You are not signed in on any other devices.')).toBeVisible();
  });

  test('refreshes session list when the user requests new data', async ({ page }) => {
    const initialDataset = [
      {
        id: 'session-phone',
        created_at: '2025-10-10T00:00:00.000Z',
        last_active_at: '2025-10-12T12:00:00.000Z',
        ip_address: '203.0.113.5',
        is_current: false,
        location: 'Houston, USA',
        device: 'Pixel 9 Pro',
      },
    ];

    const refreshedDataset = [
      {
        id: 'session-laptop',
        created_at: '2025-10-12T14:00:00.000Z',
        last_active_at: '2025-10-12T14:05:00.000Z',
        ip_address: '203.0.113.55',
        is_current: false,
        location: 'San Antonio, USA',
        device: 'Surface Laptop',
      },
    ];

    let requestCount = 0;
    await page.route('**/auth/sessions', async (route) => {
      requestCount += 1;
      const body = requestCount === 1 ? initialDataset : refreshedDataset;
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
    });

    await page.goto('/dashboard/sessions');
    await expect(page.getByText('Pixel 9 Pro')).toBeVisible();

    await page.getByRole('button', { name: 'Refresh list' }).click();
    await expect(page.getByText('Loading active sessions…')).toBeVisible();
    await expect(page.getByText('Surface Laptop')).toBeVisible();
    await expect(page.locator('text=Pixel 9 Pro')).toHaveCount(0);
  });
});
