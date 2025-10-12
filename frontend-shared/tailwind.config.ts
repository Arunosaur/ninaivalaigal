import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/**/*.{ts,tsx}",
    "./.storybook/**/*.{ts,tsx}"
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#4C6EF5",
          foreground: "#FFFFFF"
        },
        secondary: {
          DEFAULT: "#1F2937",
          foreground: "#F9FAFB"
        },
        accent: {
          DEFAULT: "#F59E0B",
          foreground: "#1F2937"
        },
        success: "#10B981",
        warning: "#F97316",
        danger: "#EF4444"
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"]
      },
      boxShadow: {
        focus: "0 0 0 3px rgba(76, 110, 245, 0.3)"
      }
    }
  },
  plugins: []
};

export default config;
