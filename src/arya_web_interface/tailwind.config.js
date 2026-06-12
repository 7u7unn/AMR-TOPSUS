/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Surfaces (darkest → lightest)
        s0: '#eef2f6',
        s1: '#f7f9fb',
        s2: '#ffffff',
        s3: '#f2f5f8',
        s4: '#e4eaf1',
        s5: '#d7e0e8',
        // Borders
        b0: '#c7d1db',
        b1: '#aebbc8',
        b2: '#8f9ead',
        b3: '#697989',
        // Cyan - Siemens (#0A6ED1)
        cy: '#0A6ED1',
        'cy-2': '#084C8D',
        'cy-bg': 'rgba(10, 110, 209, .10)',
        'cy-glo': 'rgba(10, 110, 209, .20)',
        // Orange - Beckhoff (#D95F02)
        or: '#D95F02',
        'or-2': '#A83E00',
        'or-bg': 'rgba(217, 95, 2, .10)',
        'or-glo': 'rgba(217, 95, 2, .18)',
        // Status
        gn: '#2E7D32',
        'gn-bg': 'rgba(46, 125, 50, .10)',
        rd: '#C62828',
        'rd-bg': 'rgba(198, 40, 40, .10)',
        yw: '#B7791F',
        'yw-bg': 'rgba(183, 121, 31, .12)',
        // Text
        t1: '#1F2A33',
        t2: '#5E6B78',
        t3: '#8794A3',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        mono: ['IBM Plex Mono', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Consolas', 'monospace'],
      },
      boxShadow: {
        'hmi': '0 8px 22px rgba(31, 42, 51, .08)',
      },
    },
  },
  plugins: [],
}