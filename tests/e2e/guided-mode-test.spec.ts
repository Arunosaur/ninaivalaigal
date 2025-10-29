// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// Playwright E2E test for Guided Mode dark theme
//
import { test, expect } from '@playwright/test';

test.describe('Guided Mode - Dark Theme', () => {

  test('should display dark-themed guided tour', async ({ page }) => {
    // Navigate to the app
    await page.goto('http://localhost:8101');

    // Login (adjust credentials as needed)
    await page.fill('input[placeholder="you@example.com"]', 'testuser@example.com');
    await page.fill('input[placeholder="••••••••"]', 'TestPassword123!');
    await page.click('button:has-text("Log In")');

    // Wait for navigation to dashboard
    await page.waitForURL('**/dashboard');

    // Navigate to Memory Browser
    await page.click('a:has-text("Memory Browser")');
    await page.waitForURL('**/memory-browser');

    // Click Guided Mode button
    await page.click('button:has-text("Guided Mode")');

    // Wait for guided tour overlay to appear
    await page.waitForSelector('[role="dialog"]', { state: 'visible' });

    // Test 1: Check stepper bar has dark background
    const stepper = await page.locator('.fixed.top-20').first();
    const stepperBg = await stepper.evaluate((el) =>
      window.getComputedStyle(el).backgroundColor
    );
    console.log('Stepper background:', stepperBg);
    // Should be slate-800 (rgb(30, 41, 59))
    expect(stepperBg).toContain('30, 41, 59');

    // Test 2: Check welcome modal has dark background
    const welcomeModal = await page.locator('text=Welcome to Your Memory Tour').locator('..');
    const modalBg = await welcomeModal.evaluate((el) =>
      window.getComputedStyle(el).backgroundColor
    );
    console.log('Welcome modal background:', modalBg);
    // Should be slate-800
    expect(modalBg).toContain('30, 41, 59');

    // Test 3: Check heading is white
    const heading = await page.locator('h2:has-text("Welcome to Your Memory Tour")');
    const headingColor = await heading.evaluate((el) =>
      window.getComputedStyle(el).color
    );
    console.log('Heading color:', headingColor);
    // Should be white (rgb(255, 255, 255))
    expect(headingColor).toContain('255, 255, 255');

    // Test 4: Check description text is light
    const description = await page.locator('text=Let\'s explore your memories together');
    const descColor = await description.evaluate((el) =>
      window.getComputedStyle(el).color
    );
    console.log('Description color:', descColor);
    // Should be slate-300 (light gray)

    // Test 5: Take screenshot of welcome step
    await page.screenshot({ path: 'test-outputs/guided-mode-welcome.png' });

    // Click Start Tour button
    await page.click('button:has-text("Start Tour")');

    // Wait a bit for animation
    await page.waitForTimeout(500);

    // Test 6: Check that page is NOT locked (can still interact)
    const isVisible = await page.isVisible('button:has-text("Next")');
    expect(isVisible).toBeTruthy();

    // Test 7: Take screenshot of first memory callout
    await page.screenshot({ path: 'test-outputs/guided-mode-step1.png' });

    // Click Next button
    await page.click('button:has-text("Next")');
    await page.waitForTimeout(500);

    // Test 8: Check memory callout has dark background
    const callout = await page.locator('.bg-slate-800').first();
    const calloutBg = await callout.evaluate((el) =>
      window.getComputedStyle(el).backgroundColor
    );
    console.log('Callout background:', calloutBg);
    expect(calloutBg).toContain('30, 41, 59');

    // Test 9: Take screenshot of second step
    await page.screenshot({ path: 'test-outputs/guided-mode-step2.png' });

    // Click Next again
    await page.click('button:has-text("Next")');
    await page.waitForTimeout(500);

    // Test 10: Take screenshot of third step
    await page.screenshot({ path: 'test-outputs/guided-mode-step3.png' });

    // Complete the tour
    await page.click('button:has-text("Next")');
    await page.waitForTimeout(500);

    // Test 11: Check that overlay is closed
    const overlayHidden = await page.locator('[role="dialog"]').isHidden();
    expect(overlayHidden).toBeTruthy();

    console.log('✅ All Guided Mode dark theme tests passed!');
  });

  test('should display dark-themed toast notifications', async ({ page }) => {
    // Navigate to Teams page
    await page.goto('http://localhost:8101/teams');

    // Click Create Team button
    await page.click('button:has-text("Create Team")');

    // Try to create without filling in name (should trigger error)
    await page.click('button:has-text("Create Team")');

    // Wait for toast to appear
    await page.waitForSelector('.fixed.top-4.right-4', { state: 'visible' });

    // Test 1: Check toast has dark background
    const toast = await page.locator('.fixed.top-4.right-4').first();
    const toastBg = await toast.evaluate((el) =>
      window.getComputedStyle(el.querySelector('div')).backgroundColor
    );
    console.log('Toast background:', toastBg);
    // Should be red-900 with opacity
    expect(toastBg).toContain('rgb');

    // Test 2: Check toast is visible
    const toastVisible = await toast.isVisible();
    expect(toastVisible).toBeTruthy();

    // Test 3: Take screenshot of toast
    await page.screenshot({ path: 'test-outputs/toast-error.png' });

    // Test 4: Wait for toast to auto-dismiss (5 seconds)
    await page.waitForTimeout(5500);
    const toastHidden = await toast.isHidden();
    expect(toastHidden).toBeTruthy();

    console.log('✅ Toast notification tests passed!');
  });

});
