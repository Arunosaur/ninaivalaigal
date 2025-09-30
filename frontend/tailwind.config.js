const tokens = require('./design/tokens.json');

// Transform design tokens to Tailwind theme
function transformTokens(tokenObj, path = []) {
  const result = {};

  for (const [key, value] of Object.entries(tokenObj)) {
    if (value.type && value.value) {
      // This is a token with a value
      result[key] = value.value;
    } else if (typeof value === 'object' && value !== null) {
      // This is a nested object, recurse
      result[key] = transformTokens(value, [...path, key]);
    }
  }

  return result;
}

const globalTokens = transformTokens(tokens.global);

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './components/**/*.{js,ts,jsx,tsx}',
    './pages/**/*.{js,ts,jsx,tsx}',
    './.storybook/**/*.{js,ts,jsx,tsx}',
    '../ui/**/*.{js,ts,jsx,tsx,html}', // Include existing UI directory
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
    // Add Tailwind plugins for better form styling and typography
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
};
