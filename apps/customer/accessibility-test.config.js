// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// Accessibility Testing Configuration
// For use with Lighthouse CI, axe, and pa11y

module.exports = {
  // URLs to test
  urls: [
    'http://localhost:5173/', // Vite default port
    'http://localhost:5173/login',
    'http://localhost:5173/signup',
    'http://localhost:5173/dashboard',
    'http://localhost:5173/memory-browser',
    'http://localhost:5173/teams',
    'http://localhost:5173/settings',
  ],

  // Lighthouse CI configuration
  lighthouse: {
    ci: {
      collect: {
        url: [
          'http://localhost:5173/',
          'http://localhost:5173/login',
          'http://localhost:5173/signup',
          'http://localhost:5173/dashboard',
        ],
        numberOfRuns: 3,
        settings: {
          preset: 'desktop',
        },
      },
      assert: {
        assertions: {
          'categories:accessibility': ['error', { minScore: 0.9 }],
          'color-contrast': 'error',
          'image-alt': 'error',
          'label': 'error',
          'aria-required-attr': 'error',
          'aria-valid-attr': 'error',
          'button-name': 'error',
          'link-name': 'error',
          'html-has-lang': 'error',
          'html-lang-valid': 'error',
        },
      },
      upload: {
        target: 'temporary-public-storage',
      },
    },
  },

  // pa11y configuration
  pa11y: {
    standard: 'WCAG2AA',
    timeout: 30000,
    wait: 1000,
    chromeLaunchConfig: {
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    },
  },

  // axe configuration
  axe: {
    tags: ['wcag2a', 'wcag2aa', 'wcag21aa'],
    timeout: 30000,
  },
};




