# SPEC-112: E2E Tests with Playwright
**Project:** Medhasys / Ninaivalaigal
**Status:** Draft
**Owner:** QA & FE Engineering
**Last Updated:** 2025-10-11

## Minimal Example

### login.spec.ts
```ts
import { test, expect } from '@playwright/test';

test('login flow', async ({ page }) => {
  await page.goto('http://localhost:3000/login');
  await page.fill('input[name="email"]', 'user@example.com');
  await page.fill('input[name="password"]', 'password123');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/dashboard/);
});
```

### playwright.config.ts
```ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  use: { baseURL: 'http://localhost:3000', headless: true },
  reporter: [['list'], ['html', { outputFolder: 'playwright-report' }]]
});
```

### .github/workflows/e2e.yml
```yaml
name: E2E
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: pnpm install
      - run: pnpm exec playwright install --with-deps
      - run: pnpm test:e2e
```
