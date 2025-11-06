// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { test, expect, Page } from '@playwright/test';

const FIXED_DATE_ISO = '2025-10-12T12:00:00.000Z';

const mockUser = {
  id: 'user-visual',
  email: 'visual.regression@example.com',
  name: 'Visual Regression User',
};

const mockMemories = [
  {
    id: 'memory-1',
    user_id: 'user-visual',
    title: 'Product Strategy Session',
    content: 'Outlined Q4 roadmap milestones and ownership.',
    category: 'work' as const,
    tags: ['roadmap', 'strategy'],
    created_at: '2025-10-05T15:30:00.000Z',
    updated_at: '2025-10-06T10:00:00.000Z',
  },
  {
    id: 'memory-2',
    user_id: 'user-visual',
    title: 'Family Weekend',
    content: 'Photos and notes from the hill country getaway.',
    category: 'personal' as const,
    tags: ['family'],
    created_at: '2025-10-09T18:45:00.000Z',
    updated_at: '2025-10-09T18:45:00.000Z',
  },
  {
    id: 'memory-3',
    user_id: 'user-visual',
    title: 'Team Sync Summary',
    content: 'Captured highlights from cross-team sync with action items.',
    category: 'shared' as const,
    tags: ['team', 'sync'],
    created_at: '2025-09-28T13:00:00.000Z',
    updated_at: '2025-09-29T09:15:00.000Z',
  },
];

const mockSessions = [
  {
    id: 'session-primary',
    created_at: '2025-10-10T09:00:00.000Z',
    last_active_at: '2025-10-12T11:45:00.000Z',
    ip_address: '192.0.2.5',
    location: 'Austin, USA',
    device: 'MacBook Pro 16"',
    is_current: true,
  },
  {
    id: 'session-secondary',
    created_at: '2025-10-08T15:00:00.000Z',
    last_active_at: '2025-10-11T21:20:00.000Z',
    ip_address: '198.51.100.34',
    location: 'Dallas, USA',
    device: 'iPad Air',
    is_current: false,
  },
];

async function freezeTime(page: Page) {
  await page.addInitScript((iso: string) => {
    const fixed = new Date(iso);
    const fixedTime = fixed.getTime();
    const OriginalDate = Date;

    class FrozenDate extends OriginalDate {
      constructor(...args: unknown[]) {
            if (args.length === 0) {
              super(fixedTime);
              return;
            }
        // @ts-ignore forwarding dynamic constructor args
        super(...args);
      }

      static now(): number {
        return fixedTime;
      }
    }

    FrozenDate.UTC = OriginalDate.UTC;
    FrozenDate.parse = OriginalDate.parse;
    Object.getOwnPropertyNames(OriginalDate).forEach((prop) => {
      if (prop === 'length' || prop === 'name' || prop === 'prototype') {
        return;
      }
      // @ts-ignore intentional assignment to copy static props
      FrozenDate[prop] = (OriginalDate as unknown as Record<string, unknown>)[prop];
    });

    Object.setPrototypeOf(FrozenDate, OriginalDate);

    // @ts-ignore override global Date for deterministic renders
    window.Date = FrozenDate;
  }, FIXED_DATE_ISO);
}

async function disableAnimations(page: Page) {
  await page.addInitScript(() => {
    const style = document.createElement('style');
    style.setAttribute('data-testid', 'disable-animations');
    style.textContent = '* { animation-duration: 0s !important; animation-delay: 0s !important; transition-duration: 0s !important; transition-delay: 0s !important; }';
    document.head.appendChild(style);
  });
}

async function seedAuthenticatedState(page: Page) {
  const now = Math.floor(new Date(FIXED_DATE_ISO).getTime() / 1000);
  await page.addInitScript((tokenState) => {
    window.localStorage?.clear();
    window.sessionStorage?.clear();
    window.localStorage?.setItem('auth_access_token', tokenState.accessToken);
    window.localStorage?.setItem('auth_refresh_token', tokenState.refreshToken);
    window.localStorage?.setItem('auth_access_token_expires', String(tokenState.accessExpires));
    window.localStorage?.setItem('auth_refresh_token_expires', String(tokenState.refreshExpires));
  }, {
    accessToken: 'visual-access-token',
    refreshToken: 'visual-refresh-token',
    accessExpires: now + 3600,
    refreshExpires: now + 7200,
  });
}

test.describe('Visual regression', () => {
  test.use({ timezoneId: 'UTC' });

  test.beforeEach(async ({ page }) => {
    await freezeTime(page);
    await disableAnimations(page);
  });

  test('login page matches baseline', async ({ page }) => {
    await page.route('**/auth/me', async (route) => {
      await route.fulfill({
        status: 401,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ detail: 'Unauthorized' }),
      });
    });

    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveScreenshot('login-page.png', { fullPage: true });
  });

  test('dashboard page matches baseline', async ({ page }) => {
    await seedAuthenticatedState(page);

    await page.route('**/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mockUser),
      });
    });

    await page.route('**/memory/memories**', async (route) => {
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mockMemories),
      });
    });

    await page.goto('/dashboard');
    await page.waitForSelector('text=Dashboard');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveScreenshot('dashboard-page.png', { fullPage: true });
  });

  test('sessions page matches baseline', async ({ page }) => {
    await seedAuthenticatedState(page);

    await page.route('**/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mockUser),
      });
    });

    await page.route('**/auth/sessions', async (route) => {
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mockSessions),
      });
    });

    await page.goto('/dashboard/sessions');
    await page.waitForSelector('text=Active Sessions');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveScreenshot('sessions-page.png', { fullPage: true });
  });
});
