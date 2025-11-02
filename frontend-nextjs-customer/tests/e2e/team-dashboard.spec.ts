// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/**
 * US#210: E2E Tests for Team Dashboard
 * 
 * Tests team dashboard functionality:
 * - Dashboard display with stats
 * - Member list
 * - Navigation links
 * - Upgrade CTA
 */

import { test, expect, Page } from '@playwright/test';

const mockUser = {
  id: 'user-dashboard-test',
  email: 'dashboard@example.com',
  name: 'Dashboard Test User',
};

const mockTeam = {
  id: 'team-dashboard-123',
  name: 'Dashboard Test Team',
  is_standalone: true,
  team_invite_code: 'DASH123',
  max_members: 10,
  current_members: 2,
  created_at: '2025-11-01T10:00:00Z',
  created_by_user_id: mockUser.id,
};

const mockMembers = [
  {
    id: 'member-1',
    user_id: mockUser.id,
    user_name: mockUser.name,
    user_email: mockUser.email,
    role: 'admin',
    joined_at: '2025-11-01T10:00:00Z',
    status: 'active',
  },
  {
    id: 'member-2',
    user_id: 'user-2',
    user_name: 'Contributor User',
    user_email: 'contributor@example.com',
    role: 'contributor',
    joined_at: '2025-11-01T11:00:00Z',
    status: 'active',
  },
];

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
    accessToken: 'dashboard-test-token',
    refreshToken: 'dashboard-test-refresh',
    accessExpires: now + 3600,
    refreshExpires: now + 7200,
  });
}

test.describe('Team Dashboard (US#210)', () => {
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

  test('should display team dashboard with all stats', async ({ page }) => {
    await page.route('**/teams/my', async (route) => {
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mockTeam),
      });
    });

    await page.route('**/teams/*/members', async (route) => {
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mockMembers),
      });
    });

    await page.goto('/team/dashboard?teamId=' + mockTeam.id);

    // Verify team name
    await expect(page.getByRole('heading', { name: mockTeam.name })).toBeVisible();

    // Verify stats cards
    await expect(page.getByText('Members')).toBeVisible();
    await expect(page.getByText(`${mockTeam.current_members} / ${mockTeam.max_members}`)).toBeVisible();
    await expect(page.getByText('Memories')).toBeVisible();
    await expect(page.getByText('Contexts')).toBeVisible();
    await expect(page.getByText('API Calls')).toBeVisible();
  });

  test('should display team members list', async ({ page }) => {
    await page.route('**/teams/my', async (route) => {
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mockTeam),
      });
    });

    await page.route('**/teams/*/members', async (route) => {
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mockMembers),
      });
    });

    await page.goto('/team/dashboard?teamId=' + mockTeam.id);

    // Check members section
    await expect(page.getByText('Team Members')).toBeVisible();

    // Check member details
    await expect(page.getByText(mockUser.name)).toBeVisible();
    await expect(page.getByText(mockUser.email)).toBeVisible();
    await expect(page.getByText('Contributor User')).toBeVisible();

    // Check role badges
    await expect(page.getByText('admin', { exact: false })).toBeVisible();
    await expect(page.getByText('contributor', { exact: false })).toBeVisible();
  });

  test('should display team information section', async ({ page }) => {
    await page.route('**/teams/my', async (route) => {
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mockTeam),
      });
    });

    await page.goto('/team/dashboard?teamId=' + mockTeam.id);

    // Check team info section
    await expect(page.getByText('Team Information')).toBeVisible();
    await expect(page.getByText('Invite Code')).toBeVisible();
    await expect(page.getByText(mockTeam.team_invite_code)).toBeVisible();
    await expect(page.getByText('Created')).toBeVisible();
    await expect(page.getByText('Status')).toBeVisible();
  });

  test('should navigate to invite page from dashboard', async ({ page }) => {
    await page.route('**/teams/my', async (route) => {
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mockTeam),
      });
    });

    await page.goto('/team/dashboard?teamId=' + mockTeam.id);

    // Click invite link
    await page.getByRole('link', { name: /Invite Member/i }).click();

    // Should navigate to invite page
    await expect(page).toHaveURL(new RegExp(`/team/${mockTeam.id}/invite`));
  });

  test('should navigate to upgrade page from dashboard', async ({ page }) => {
    await page.route('**/teams/my', async (route) => {
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mockTeam),
      });
    });

    await page.goto('/team/dashboard?teamId=' + mockTeam.id);

    // Click upgrade button
    await page.getByRole('link', { name: /Upgrade to Organization/i }).click();

    // Should navigate to upgrade page
    await expect(page).toHaveURL(new RegExp(`/team/${mockTeam.id}/upgrade`));
  });

  test('should show upgrade CTA for standalone teams', async ({ page }) => {
    await page.route('**/teams/my', async (route) => {
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...mockTeam, is_standalone: true }),
      });
    });

    await page.goto('/team/dashboard?teamId=' + mockTeam.id);

    // Should show upgrade banner
    await expect(page.getByText(/Ready to Scale/i)).toBeVisible();
    await expect(page.getByText(/Upgrade to an organization/i)).toBeVisible();
  });

  test('should show loading state while fetching team data', async ({ page }) => {
    // Delay API response
    await page.route('**/teams/my', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 300));
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mockTeam),
      });
    });

    await page.goto('/team/dashboard?teamId=' + mockTeam.id);

    // Should show loading indicator
    await expect(page.getByText(/Loading team data/i)).toBeVisible();
  });

  test('should handle empty members list', async ({ page }) => {
    await page.route('**/teams/my', async (route) => {
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mockTeam),
      });
    });

    await page.route('**/teams/*/members', async (route) => {
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify([]),
      });
    });

    await page.goto('/team/dashboard?teamId=' + mockTeam.id);

    // Should show empty state
    await expect(page.getByText(/No members yet/i)).toBeVisible();
  });
});

