/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        cyber: {
          bg: "#090D16",
          card: "#0E1322",
          border: "#1E293B",
          primary: "#00F2FE",
          secondary: "#4FACFE",
          accent: "#10B981",
          warning: "#F59E0B",
          danger: "#F43F5E",
          muted: "#64748B",
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
