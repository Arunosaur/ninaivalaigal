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

    // Wait for dashboard to load
    await page.waitForSelector('h1', { state: 'visible' });

    // Verify team name
    await expect(page.getByRole('heading', { name: mockTeam.name })).toBeVisible({ timeout: 10000 });

    // Verify stats cards (they may load asynchronously)
    await expect(page.locator('text=/Members/i').first()).toBeVisible({ timeout: 5000 });
    await expect(page.locator(`text=${mockTeam.current_members} / ${mockTeam.max_members}`)).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=/Memories/i').first()).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=/Contexts/i').first()).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=/API Calls/i').first()).toBeVisible({ timeout: 5000 });
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

    // Wait for dashboard to load
    await page.waitForSelector('h1', { state: 'visible' });

    // Check members section
    await expect(page.getByText('Team Members')).toBeVisible({ timeout: 10000 });

    // Check member details (wait for members to load)
    await expect(page.locator(`text=${mockUser.name}`).first()).toBeVisible({ timeout: 5000 });
    await expect(page.locator(`text=${mockUser.email}`).first()).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=Contributor User').first()).toBeVisible({ timeout: 5000 });

    // Check role badges
    await expect(page.locator('text=/admin/i').first()).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=/contributor/i').first()).toBeVisible({ timeout: 5000 });
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

    // Wait for dashboard to load
    await page.waitForSelector('h1', { state: 'visible' });

    // Check team info section
    await expect(page.getByText('Team Information')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=/Invite Code/i').first()).toBeVisible({ timeout: 5000 });
    await expect(page.locator(`text=${mockTeam.team_invite_code}`).first()).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=/Created/i').first()).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=/Status/i').first()).toBeVisible({ timeout: 5000 });
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

    // Wait for dashboard to load
    await page.waitForSelector('h1', { state: 'visible' });

    // Click invite link (may be text link or button)
    const inviteLink = page.getByRole('link', { name: /Invite Member/i }).or(
      page.locator('a[href*="/invite"]')
    );
    await inviteLink.first().click();

    // Should navigate to invite page
    await expect(page).toHaveURL(new RegExp(`/team/${mockTeam.id}/invite`), { timeout: 5000 });
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

    // Wait for dashboard to load
    await page.waitForSelector('h1', { state: 'visible' });

    // Click upgrade button (may be in header or CTA section)
    const upgradeLink = page.getByRole('link', { name: /Upgrade to Organization/i }).or(
      page.locator('a[href*="/upgrade"]')
    );
    await upgradeLink.first().click();

    // Should navigate to upgrade page
    await expect(page).toHaveURL(new RegExp(`/team/${mockTeam.id}/upgrade`), { timeout: 5000 });
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

    // Should show upgrade banner (check for upgrade CTA section)
    const upgradeSection = page.locator('text=/Ready to Scale|Upgrade to an organization/i').first();
    await expect(upgradeSection).toBeVisible({ timeout: 10000 });
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

    // Should show empty state (check for empty members message)
    await expect(page.locator('text=/No members|No members yet/i').first()).toBeVisible();
  });
});

