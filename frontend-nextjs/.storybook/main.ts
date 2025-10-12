// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import type { StorybookConfig } from '@storybook/react-webpack5';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

const config: StorybookConfig = {
  stories: ['../src/components/**/*.stories.@(js|jsx|ts|tsx|mdx)'],
  addons: [
    '@storybook/addon-links',
    '@storybook/addon-essentials',
    '@storybook/addon-interactions',
    '@storybook/addon-a11y', // Accessibility testing
  ],
  framework: {
    name: '@storybook/react-webpack5',
    options: {},
  },
  docs: {
    autodocs: 'tag',
  },
  typescript: {
    check: false,
    reactDocgen: 'react-docgen-typescript',
    reactDocgenTypescriptOptions: {
      shouldExtractLiteralValuesFromEnum: true,
      propFilter: (prop) => (prop.parent ? !/node_modules/.test(prop.parent.fileName) : true),
    },
  },
  webpackFinal: async (config) => {
    // Add path aliases to match tsconfig
    if (config.resolve) {
      config.resolve.alias = {
        ...config.resolve.alias,
        '@/components': join(__dirname, '../src/components'),
        '@/app': join(__dirname, '../src/app'),
        '@/hooks': join(__dirname, '../src/hooks'),
        '@/utils': join(__dirname, '../src/utils'),
        '@/lib': join(__dirname, '../src/lib'),
        '@/styles': join(__dirname, '../src/styles'),
      };
    }
    return config;
  },
};

export default config;
