import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        display: ["var(--font-display)", "Georgia", "serif"],
      },
      colors: {
        ember: {
          50: "#fff4ed",
          100: "#ffe6d5",
          200: "#fecdaa",
          300: "#fdaa74",
          400: "#fb7d3c",
          500: "#f4562a",
          600: "#e13d16",
          700: "#bb2d14",
          800: "#952518",
          900: "#792116",
        },
      },
      boxShadow: {
        soft: "0 1px 1px rgba(15, 23, 42, 0.03), 0 6px 20px -6px rgba(15, 23, 42, 0.10)",
        "soft-lg": "0 2px 4px rgba(15, 23, 42, 0.04), 0 24px 48px -16px rgba(15, 23, 42, 0.20)",
      },
      backgroundImage: {
        grain:
          "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.9'/%3E%3C/svg%3E\")",
      },
    },
  },
  plugins: [],
};

export default config;
