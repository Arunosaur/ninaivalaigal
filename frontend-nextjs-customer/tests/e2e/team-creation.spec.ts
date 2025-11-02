// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/**
 * US#210: E2E Tests for Team Creation Flow UI
 *
 * Tests the complete team creation wizard and related flows:
 * - Team creation wizard (3 steps)
 * - Team dashboard display
 * - Member invitations
 * - Upgrade to organization
 */

import { test, expect, Page } from '@playwright/test';

const mockUser = {
  id: 'user-team-test',
  email: 'teamtest@example.com',
  name: 'Team Test User',
};

const mockTeam = {
  id: 'team-123',
  name: 'Test Team',
  is_standalone: true,
  team_invite_code: 'INV123',
  max_members: 10,
  current_members: 1,
  created_at: '2025-11-01T12:00:00Z',
  created_by_user_id: mockUser.id,
};

const mockMembers = [
  {
    id: 'member-1',
    user_id: mockUser.id,
    user_name: mockUser.name,
    user_email: mockUser.email,
    role: 'admin',
    joined_at: '2025-11-01T12:00:00Z',
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
    accessToken: 'team-test-token',
    refreshToken: 'team-test-refresh',
    accessExpires: now + 3600,
    refreshExpires: now + 7200,
  });
}

test.describe('Team Creation Flow (US#210)', () => {
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
  });

  test('should display team creation wizard with 3 steps', async ({ page }) => {
    await page.goto('/team/create');

    // Check page title
    await expect(page.getByRole('heading', { name: /Create Your Team/i })).toBeVisible();

    // Check progress indicator shows 3 steps
    const stepIndicators = page.locator('text=/^[123]$/').filter({ has: page.locator('..') });
    await expect(stepIndicators).toHaveCount(3);

    // Check step labels (using more specific selectors)
    await expect(page.locator('text=Team Info').first()).toBeVisible();
    await expect(page.locator('text=Invite Members').first()).toBeVisible();
    await expect(page.locator('text=Review').first()).toBeVisible();
  });

  test('should validate team name in step 1', async ({ page }) => {
    await page.goto('/team/create');

    // Try to proceed with empty name
    await page.getByRole('button', { name: 'Next' }).click();

    // Should show validation error
    await expect(page.getByText(/Team name must be at least/i)).toBeVisible();
  });

  test('should complete team creation wizard successfully', async ({ page }) => {
    // Mock team creation API
    await page.route('**/teams/create-standalone', async (route) => {
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mockTeam),
      });
    });

    await page.goto('/team/create');

    // Step 1: Fill team information
    await page.getByLabel(/Team Name/i).fill('My Awesome Team');
    await page.getByLabel(/Description/i).fill('A test team for collaboration');
    await page.getByLabel(/Maximum Members/i).fill('15');

    // Navigate to step 2
    await page.getByRole('button', { name: 'Next' }).click();

    // Verify we're on step 2
    await expect(page.getByText('Invite Team Members')).toBeVisible();

    // Skip invitations (optional step)
    await page.getByRole('button', { name: 'Next' }).click();

    // Verify we're on step 3
    await expect(page.getByText('Review Your Team')).toBeVisible();
    await expect(page.getByText('My Awesome Team')).toBeVisible();

    // Create team
    await page.getByRole('button', { name: /Create Team/i }).click();

    // Should navigate to dashboard
    await expect(page).toHaveURL(/team\/dashboard/);
  });

  test('should allow adding member invitations in step 2', async ({ page }) => {
    await page.goto('/team/create');

    // Step 1: Fill team information
    await page.getByLabel(/Team Name/i).fill('Test Team');
    await page.getByLabel(/Maximum Members/i).fill('10');
    await page.getByRole('button', { name: 'Next' }).click();

    // Step 2: Add invitation
    const emailInput = page.getByPlaceholder(/Enter email address/i).or(page.locator('input[type="email"]'));
    await emailInput.fill('member@example.com');

    // Find the role select dropdown
    const roleSelect = page.locator('select').first();
    await roleSelect.selectOption('contributor');

    await page.getByRole('button', { name: 'Add' }).click();

    // Verify invitation appears in list
    await expect(page.getByText('member@example.com')).toBeVisible();
    await expect(page.getByText('(contributor)')).toBeVisible();
  });

  test('should display team dashboard with stats', async ({ page }) => {
    // Mock team data API
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

    // Check team name is displayed
    await expect(page.getByRole('heading', { name: mockTeam.name })).toBeVisible({ timeout: 10000 });

    // Check stats cards (they may load asynchronously)
    await expect(page.locator('text=/Members|Members:/i').first()).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=/Memories|Memories:/i').first()).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=/Contexts|Contexts:/i').first()).toBeVisible({ timeout: 5000 });

    // Check members list
    await expect(page.getByText('Team Members')).toBeVisible();
  });

  test('should handle team dashboard when user has no team', async ({ page }) => {
    // Mock no team response
    await page.route('**/teams/my', async (route) => {
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(null),
      });
    });

    await page.goto('/team/dashboard');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Should show "Team Not Found" message (wait for it)
    await expect(page.locator('text=/Team Not Found|don\'t have a team|You don\'t have/i').first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByRole('link', { name: /Create Your First Team|Create/i })).toBeVisible({ timeout: 5000 });
  });

  test('should send team invitation successfully', async ({ page }) => {
    // Mock team data
    await page.route('**/teams/my', async (route) => {
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mockTeam),
      });
    });

    // Mock invitation API
    let invitationSent = false;
    await page.route('**/teams/invite', async (route) => {
      invitationSent = true;
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: 'inv-1',
          email: 'newmember@example.com',
          role: 'contributor',
          status: 'pending',
          expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
          created_at: new Date().toISOString(),
          invited_by_name: mockUser.name,
        }),
      });
    });

    await page.goto(`/team/${mockTeam.id}/invite`);

    // Wait for page to load
    await page.waitForSelector('input[type="email"]', { state: 'visible' });

    // Fill invitation form
    await page.locator('input[type="email"]').fill('newmember@example.com');
    await page.locator('select').first().selectOption('contributor');

    // Submit invitation
    await page.getByRole('button', { name: /Send Invitation/i }).click();

    // Verify success message
    await expect(page.locator('text=/Invitation sent|success/i').first()).toBeVisible({ timeout: 5000 });
    expect(invitationSent).toBe(true);
  });

  test('should validate email format in invitation form', async ({ page }) => {
    await page.route('**/teams/my', async (route) => {
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mockTeam),
      });
    });

    await page.goto(`/team/${mockTeam.id}/invite`);

    // Wait for page to load
    await page.waitForSelector('input[type="email"]', { state: 'visible' });

    // Try invalid email - HTML5 validation should prevent submission
    const emailInput = page.locator('input[type="email"]');
    await emailInput.fill('invalid-email');

    // Try to submit - browser validation should prevent it
    const submitButton = page.getByRole('button', { name: /Send Invitation/i });
    await submitButton.click();

    // Check for HTML5 validation (the input should be marked as invalid)
    await expect(emailInput).toHaveAttribute('type', 'email');
    // HTML5 validation might show a tooltip, or check if form submission was prevented
    const validity = await emailInput.evaluate((el: HTMLInputElement) => el.validity.valid);
    expect(validity).toBe(false);
  });

  test('should display upgrade to organization form', async ({ page }) => {
    await page.goto(`/team/${mockTeam.id}/upgrade`);

    // Check form fields
    await expect(page.getByLabel(/Organization Name/i)).toBeVisible();
    await expect(page.getByLabel(/Domain/i)).toBeVisible();
    await expect(page.getByLabel(/Organization Size/i)).toBeVisible();
    await expect(page.getByLabel(/Industry/i)).toBeVisible();

    // Check benefits section
    await expect(page.getByText(/What You'll Get/i)).toBeVisible();
  });

  test('should upgrade team to organization successfully', async ({ page }) => {
    const mockOrg = {
      id: 'org-123',
      name: 'Test Organization',
      domain: 'example.com',
    };

    // Mock upgrade API
    await page.route(`**/teams/${mockTeam.id}/upgrade-to-org`, async (route) => {
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          success: true,
          message: 'Team successfully upgraded',
          organization: mockOrg,
        }),
      });
    });

    await page.goto(`/team/${mockTeam.id}/upgrade`);

    // Fill upgrade form
    await page.getByLabel(/Organization Name/i).fill(mockOrg.name);
    await page.getByLabel(/Domain/i).fill(mockOrg.domain);
    await page.getByLabel(/Organization Size/i).selectOption('startup');

    // Submit
    await page.getByRole('button', { name: /Upgrade to Organization/i }).click();

    // Should navigate to organization page (if exists)
    // For now, just verify API was called
    await expect(page).toHaveURL(/organization/);
  });

  test('should validate required fields in upgrade form', async ({ page }) => {
    await page.goto(`/team/${mockTeam.id}/upgrade`);

    // Wait for form to load
    await page.waitForSelector('input[type="text"]', { state: 'visible' });

    // Find organization name input (should have required attribute)
    const orgNameInput = page.locator('input').filter({ hasText: /Organization Name/i }).or(
      page.locator('label:has-text("Organization Name") + input').or(
        page.locator('input[required]').first()
      )
    );

    // Check that it has required attribute
    const isRequired = await orgNameInput.first().evaluate((el: HTMLElement) => {
      return el.hasAttribute('required') || (el as HTMLInputElement).required;
    });

    // HTML5 validation should be present
    expect(isRequired).toBeTruthy();
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Mock API error
    await page.route('**/teams/create-standalone', async (route) => {
      await route.fulfill({
        status: 400,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: 'User already has a standalone team' }),
      });
    });

    await page.goto('/team/create');

    // Wait for page to load
    await page.waitForSelector('input[type="text"]', { state: 'visible' });

    // Fill and submit form
    await page.getByLabel(/Team Name/i).fill('Test Team');
    await page.getByRole('button', { name: 'Next' }).click();
    await page.getByRole('button', { name: 'Next' }).click();

    // Wait for create button to be enabled
    await page.waitForSelector('button:has-text("Create Team")', { state: 'visible' });
    await page.getByRole('button', { name: /Create Team/i }).click();

    // Should display error message (wait for it to appear)
    await expect(page.locator('text=/already has|error|failed/i').first()).toBeVisible({ timeout: 5000 });
  });

  test('should show loading state during team creation', async ({ page }) => {
    // Delay API response to see loading state
    await page.route('**/teams/create-standalone', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 500));
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mockTeam),
      });
    });

    await page.goto('/team/create');

    // Complete wizard
    await page.getByLabel(/Team Name/i).fill('Test Team');
    await page.getByRole('button', { name: 'Next' }).click();
    await page.getByRole('button', { name: 'Next' }).click();
    await page.getByRole('button', { name: /Create Team/i }).click();

    // Should show loading state
    await expect(page.getByRole('button', { name: /Creating.../i })).toBeVisible();
  });
});
