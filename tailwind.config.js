/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  safelist: [
    'row-span-1',
    'row-span-2',
    'row-span-3',
    'row-span-4',
  ],
  theme: {
    extend: {
      colors: {
        dashboard: {
          bg: '#0F1218',
          panel: '#1A1F2B',
          panelBorder: '#293245',
          text: '#E2E8F0',
          muted: '#94A3B8',
          accent: '#0EA5E9',
          danger: '#EF4444',
          warning: '#F59E0B',
          success: '#10B981'
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      }
    },
  },
  plugins: [],
}
