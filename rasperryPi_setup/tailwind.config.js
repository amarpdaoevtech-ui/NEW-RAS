/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'dashboard-bg': '#0a0a0a',
        'dashboard-card': '#1a1a1a',
        'neon-cyan': '#00f2ff',
        'neon-green': '#00ff9d',
        'neon-blue': '#0066ff',
        'neon-orange': '#ff5e00',
        'neon-red': '#ff0000',
      },
      fontFamily: {
        'sans': ['Inter', 'sans-serif'],
        'mono': ['Roboto Mono', 'monospace'],
      }
    },
  },
  plugins: [],
}
