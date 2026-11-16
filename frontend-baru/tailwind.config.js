/** @type {import('tailwindcss').Config} */

// Netral hangat keunguan, diturunkan dari palet landing page.
// gray & slate dipetakan ke skala yang sama supaya kelas lama tetap selaras.
const plum = {
  50: '#f7f1e7',
  100: '#f0e7dc',
  200: '#e7ddd0',
  300: '#d6c6d6',
  400: '#a591ad',
  500: '#7d6b88',
  600: '#5e4d6e',
  700: '#4a3a5a',
  800: '#352748',
  900: '#2a1d3b',
  950: '#1d1429',
};

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        glowmatch: {
          primary: '#6b46c1',
          secondary: '#2a1d3b',
          background: '#fbf7ec',
        },
        paper: '#fbf7ec',
        ink: '#2a1d3b',
        brand: '#6b46c1',
        accent: '#aa2870',
        coral: '#f69179',
        peri: '#96a8e0',
        olive: '#7e8a59',
        line: '#e7ddd0',
        chip: '#f0e4ee',
        gray: plum,
        slate: plum,
        purple: {
          50: '#f6eef4',
          100: '#f0e4ee',
          200: '#e2cde0',
          300: '#c9a9cb',
          400: '#a882b4',
          500: '#8a5fb8',
          600: '#6b46c1',
          700: '#553596',
          800: '#3d2a54',
          900: '#2a1d3b',
        },
      },
      fontFamily: {
        sans: ['"DM Sans"', 'system-ui', 'sans-serif'],
        serif: ['"Instrument Serif"', 'Georgia', 'serif'],
      },
      keyframes: {
        scan: {
          '0%, 100%': { transform: 'translateY(0%)' },
          '50%': { transform: 'translateY(400px)' },
        },
      },
      animation: {
        scan: 'scan 3s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
