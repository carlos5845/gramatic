import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brutal: {
          bg: "#D9F5EE",        // Pastel mint background from reference
          bgDarker: "#C4EDE4",
          dark: "#0F172A",      // Solid border and text dark
          yellow: "#FEE166",    // Accent yellow
          yellowHover: "#FCD34D",
          pink: "#FFA8C5",      // Accent pink/rose
          pinkLight: "#FFE4EE",
          blue: "#2B59FF",      // Electric blue
          blueHover: "#1E47E6",
          blueLight: "#E8EFFF",
          teal: "#14B8A6",      // Teal accent
          tealLight: "#CCFBF1",
          card: "#FFFFFF",
        },
        brand: {
          50: "#eef2ff",
          100: "#e0e7ff",
          200: "#c7d2fe",
          300: "#a5b4fc",
          400: "#818cf8",
          500: "#6366f1",
          600: "#4f46e5",
          700: "#4338ca",
          800: "#3730a3",
          900: "#312e81",
        },
      },
      boxShadow: {
        "brutal-xs": "1.5px 1.5px 0px #0F172A",
        "brutal-sm": "2px 2px 0px #0F172A",
        "brutal": "3.5px 3.5px 0px #0F172A",
        "brutal-lg": "5px 5px 0px #0F172A",
        "brutal-blue": "3.5px 3.5px 0px #1E40AF",
      },
      borderWidth: {
        "1.5": "1.5px",
        "2": "2px",
        "2.5": "2.5px",
        "3": "3px",
      },
    },
  },
  plugins: [],
};

export default config;
