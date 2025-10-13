// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import { test, expect } from '@playwright/test';

test.describe('Authentication flows', () => {
  test('user can sign in successfully', async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage?.clear();
      window.sessionStorage?.clear();
    });

    await page.route('**/auth/login', async (route) => {
      const body = JSON.stringify({
        access_token: 'mock-token',
        token_type: 'bearer',
        expires_in: 3600,
        refresh_token: 'mock-refresh',
        refresh_expires_in: 7200,
      });
      await route.fulfill({ status: 200, body, headers: { 'Content-Type': 'application/json' } });
    });

    await page.route('**/auth/me', async (route) => {
      const body = JSON.stringify({
        id: '1',
        email: 'demo@example.com',
        name: 'Demo User',
        emailVerified: true,
      });
      await route.fulfill({ status: 200, body, headers: { 'Content-Type': 'application/json' } });
    });

  await page.goto('/login');

  const emailInput = page.getByLabel('Email address');
  const passwordInput = page.getByLabel('Password', { exact: true });
  const submitButton = page.getByRole('button', { name: 'Sign in' });

  await expect(emailInput).toBeEnabled();
  await expect(passwordInput).toBeEnabled();
  await expect(submitButton).toBeEnabled();

  await emailInput.fill('demo@example.com');
  await passwordInput.fill('password123');
  await submitButton.click();

    await expect(page).toHaveURL(/dashboard/);
  });

  test('user can sign up and be redirected to dashboard', async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage?.clear();
      window.sessionStorage?.clear();
    });

    await page.route('**/auth/signup/individual', async (route) => {
      const body = JSON.stringify({
        success: true,
        message: 'Account created',
        user: {
          user_id: 5,
          email: 'new@example.com',
          name: 'New User',
          account_type: 'individual',
          jwt_token: 'new-mock-token',
          email_verified: false,
        },
      });
      await route.fulfill({ status: 200, body, headers: { 'Content-Type': 'application/json' } });
    });

    await page.route('**/auth/me', async (route) => {
      const body = JSON.stringify({
        id: '5',
        email: 'new@example.com',
        name: 'New User',
        emailVerified: false,
      });
      await route.fulfill({ status: 200, body, headers: { 'Content-Type': 'application/json' } });
    });

    await page.goto('/signup');

    const signupEmail = page.getByLabel('Email address');
    const signupDisplayName = page.getByLabel('Display name (optional)');
    const signupPassword = page.getByLabel('Password', { exact: true });
    const signupConfirm = page.getByLabel('Confirm password');
    const signupSubmit = page.getByRole('button', { name: 'Register' });

    await expect(signupEmail).toBeEnabled();
    await expect(signupDisplayName).toBeEnabled();
    await expect(signupPassword).toBeEnabled();
    await expect(signupConfirm).toBeEnabled();
    await expect(signupSubmit).toBeEnabled();

    await signupEmail.fill('new@example.com');
    await signupDisplayName.fill('Newbie');
    await signupPassword.fill('Password123');
    await signupConfirm.fill('Password123');
    await signupSubmit.click();

    await expect(page).toHaveURL(/dashboard/);
  });
});
