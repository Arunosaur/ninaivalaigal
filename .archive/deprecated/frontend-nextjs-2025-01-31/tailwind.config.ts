// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import type { Config } from 'tailwindcss';
import tokens from './design/tokens.json';

// Transform design tokens to Tailwind theme
function transformTokens(tokenObj: any, path: string[] = []): any {
  const result: any = {};

  for (const [key, value] of Object.entries(tokenObj)) {
    if ((value as any).type && (value as any).value) {
      // This is a token with a value
      result[key] = (value as any).value;
    } else if (typeof value === 'object' && value !== null) {
      // This is a nested object, recurse
      result[key] = transformTokens(value, [...path, key]);
    }
  }

  return result;
}

const globalTokens = transformTokens(tokens.global);

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    './.storybook/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        ...globalTokens.colors,
        // Semantic color mappings for easier use
        primary: globalTokens.colors.primary,
        secondary: globalTokens.colors.secondary,
        success: globalTokens.colors.success,
        warning: globalTokens.colors.warning,
        error: globalTokens.colors.error,
      },
      spacing: globalTokens.spacing,
      borderRadius: globalTokens.borderRadius,
      fontFamily: globalTokens.fontFamily,
      fontSize: globalTokens.fontSize,
      fontWeight: globalTokens.fontWeight,
      lineHeight: globalTokens.lineHeight,
      boxShadow: globalTokens.boxShadow,
      transitionDuration: {
        fast: '150ms',
        base: '200ms',
        slow: '300ms',
      },
      transitionTimingFunction: {
        'ease-in-out': 'ease-in-out',
      },
    },
  },
  plugins: [
    // @ts-ignore - CommonJS modules in Tailwind config
    require('@tailwindcss/forms'),
    // @ts-ignore - CommonJS modules in Tailwind config
    require('@tailwindcss/typography'),
  ],
};

export default config;
