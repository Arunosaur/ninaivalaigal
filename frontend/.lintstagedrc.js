// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
/**
 * Lint-staged Configuration
 * Part of SPEC-096: Frontend Quality Enforcement & CI/CD
 *
 * Runs linters on git staged files only for fast pre-commit checks
 */

module.exports = {
  // JavaScript/TypeScript files
  '*.{js,jsx,ts,tsx}': [
    'eslint --fix',
    'prettier --write',
    // Run type check (will check whole project, but fast enough)
    () => 'tsc --noEmit',
  ],

  // CSS/SCSS files
  '*.{css,scss}': [
    'stylelint --fix',
    'prettier --write',
  ],

  // JSON files
  '*.json': [
    'prettier --write',
  ],

  // Markdown files
  '*.md': [
    'prettier --write',
  ],

  // Test files - run related tests
  '*.{test,spec}.{js,jsx,ts,tsx}': [
    'jest --bail --findRelatedTests --passWithNoTests',
  ],
};
