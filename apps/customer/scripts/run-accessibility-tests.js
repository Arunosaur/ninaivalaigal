#!/usr/bin/env node
// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// Automated Accessibility Testing Script
// Runs Lighthouse, axe, and pa11y tests

import { exec } from 'child_process';
import { promisify } from 'util';
import http from 'http';

const execAsync = promisify(exec);

const BASE_URL = 'http://localhost:8101';
const PAGES = [
  { path: '/', name: 'Home' },
  { path: '/login', name: 'Login' },
  { path: '/signup', name: 'Signup' },
  { path: '/dashboard', name: 'Dashboard' },
  { path: '/memory-browser', name: 'Memory Browser' },
  { path: '/teams', name: 'Teams' },
  { path: '/settings', name: 'Settings' },
];

// Check if server is running
async function checkServer(url) {
  return new Promise((resolve) => {
    const req = http.get(url, (res) => {
      resolve(res.statusCode === 200 || res.statusCode === 307 || res.statusCode === 302);
    });
    req.on('error', () => resolve(false));
    req.setTimeout(3000, () => {
      req.destroy();
      resolve(false);
    });
  });
}

// Wait for server to be ready
async function waitForServer(maxAttempts = 30) {
  console.log('⏳ Waiting for dev server to be ready...');
  for (let i = 0; i < maxAttempts; i++) {
    const isReady = await checkServer(BASE_URL);
    if (isReady) {
      console.log('✅ Server is ready!\n');
      return true;
    }
    await new Promise((resolve) => setTimeout(resolve, 1000));
    process.stdout.write('.');
  }
  console.log('\n❌ Server not ready after 30 seconds');
  return false;
}

// Run Lighthouse test
async function runLighthouse(url, name) {
  console.log(`\n🔍 Running Lighthouse on ${name}...`);
  try {
    const { stdout } = await execAsync(
      `npx lighthouse "${url}" --only-categories=accessibility --output=json --quiet --chrome-flags="--headless --no-sandbox"`
    );
    const result = JSON.parse(stdout);
    const score = result.categories.accessibility.score * 100;

    console.log(`   Accessibility Score: ${score.toFixed(0)}/100`);

    if (score >= 90) {
      console.log(`   ✅ PASS (≥90)`);
    } else {
      console.log(`   ⚠️  WARNING (<90)`);
    }

    // Report issues
    if (result.audits && Object.keys(result.audits).length > 0) {
      const issues = Object.values(result.audits)
        .filter((audit) => audit.score !== null && audit.score < 1)
        .map((audit) => ({
          id: audit.id,
          title: audit.title,
          description: audit.description,
        }));

      if (issues.length > 0) {
        console.log(`   Issues found: ${issues.length}`);
        issues.slice(0, 3).forEach((issue) => {
          console.log(`   - ${issue.title}`);
        });
      }
    }

    return { score, passed: score >= 90 };
  } catch (error) {
    console.log(`   ❌ Error: ${error.message}`);
    return { score: 0, passed: false };
  }
}

// Run axe test
async function runAxe(url, name) {
  console.log(`\n🔍 Running axe on ${name}...`);
  try {
    const { stdout } = await execAsync(
      `npx @axe-core/cli "${url}" --tags wcag2a,wcag2aa,wcag21aa --timeout 30000`
    );

    const violationCount = (stdout.match(/violations/i) || []).length;
    const hasViolations = stdout.toLowerCase().includes('violation');

    if (!hasViolations || violationCount === 0) {
      console.log(`   ✅ PASS (0 violations)`);
      return { violations: 0, passed: true };
    } else {
      console.log(`   ⚠️  WARNING (violations found)`);
      console.log(`   ${stdout.substring(0, 200)}...`);
      return { violations: violationCount, passed: false };
    }
  } catch (error) {
    // axe CLI may exit with code 1 if violations found
    if (error.stdout) {
      const violationCount = (error.stdout.match(/violations/i) || []).length;
      console.log(`   ⚠️  WARNING (violations found)`);
      return { violations: violationCount, passed: false };
    }
    console.log(`   ❌ Error: ${error.message}`);
    return { violations: -1, passed: false };
  }
}

// Run pa11y test
async function runPa11y(url, name) {
  console.log(`\n🔍 Running pa11y on ${name}...`);
  try {
    const { stdout } = await execAsync(
      `npx pa11y "${url}" --standard WCAG2AA --timeout 30000 --reporter json`
    );

    let result;
    try {
      result = JSON.parse(stdout);
    } catch {
      // pa11y may output non-JSON for success
      if (stdout.toLowerCase().includes('no issues') || stdout.trim() === '') {
        console.log(`   ✅ PASS (0 issues)`);
        return { issues: 0, passed: true };
      }
      console.log(`   ⚠️  WARNING (check output)`);
      return { issues: -1, passed: false };
    }

    const issues = result.issues || [];
    if (issues.length === 0) {
      console.log(`   ✅ PASS (0 issues)`);
      return { issues: 0, passed: true };
    } else {
      console.log(`   ⚠️  WARNING (${issues.length} issues)`);
      issues.slice(0, 3).forEach((issue) => {
        console.log(`   - ${issue.message}`);
      });
      return { issues: issues.length, passed: false };
    }
  } catch (error) {
    if (error.stdout) {
      try {
        const result = JSON.parse(error.stdout);
        const issues = result.issues || [];
        console.log(`   ⚠️  WARNING (${issues.length} issues)`);
        return { issues: issues.length, passed: false };
      } catch {
        console.log(`   ⚠️  WARNING (check output)`);
        return { issues: -1, passed: false };
      }
    }
    console.log(`   ❌ Error: ${error.message}`);
    return { issues: -1, passed: false };
  }
}

// Main test runner
async function runTests() {
  console.log('========================================');
  console.log('Accessibility Testing - Customer UI');
  console.log('========================================\n');

  // Check if server is running
  const serverReady = await waitForServer();
  if (!serverReady) {
    console.log('\n❌ Please start the dev server first:');
    console.log('   cd apps/customer && npm run dev\n');
    process.exit(1);
  }

  const results = {
    lighthouse: [],
    axe: [],
    pa11y: [],
  };

  // Test each page
  for (const page of PAGES) {
    const url = `${BASE_URL}${page.path}`;
    console.log(`\n📄 Testing: ${page.name} (${page.path})`);
    console.log('─'.repeat(50));

    // Run all tests
    const lighthouseResult = await runLighthouse(url, page.name);
    const axeResult = await runAxe(url, page.name);
    const pa11yResult = await runPa11y(url, page.name);

    results.lighthouse.push({ page: page.name, ...lighthouseResult });
    results.axe.push({ page: page.name, ...axeResult });
    results.pa11y.push({ page: page.name, ...pa11yResult });

    // Small delay between pages
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }

  // Summary
  console.log('\n' + '='.repeat(50));
  console.log('📊 Test Summary');
  console.log('='.repeat(50));

  const lighthousePassed = results.lighthouse.filter((r) => r.passed).length;
  const axePassed = results.axe.filter((r) => r.passed).length;
  const pa11yPassed = results.pa11y.filter((r) => r.passed).length;

  console.log(`\nLighthouse: ${lighthousePassed}/${results.lighthouse.length} pages passed`);
  console.log(`axe:        ${axePassed}/${results.axe.length} pages passed`);
  console.log(`pa11y:      ${pa11yPassed}/${results.pa11y.length} pages passed`);

  const allPassed = lighthousePassed === results.lighthouse.length &&
                     axePassed === results.axe.length &&
                     pa11yPassed === results.pa11y.length;

  if (allPassed) {
    console.log('\n✅ All tests passed!');
    process.exit(0);
  } else {
    console.log('\n⚠️  Some tests had issues. Review the output above.');
    process.exit(1);
  }
}

// Run tests
runTests().catch((error) => {
  console.error('❌ Fatal error:', error);
  process.exit(1);
});
