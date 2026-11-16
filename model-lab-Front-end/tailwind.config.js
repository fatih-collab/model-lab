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
        sans: ['"DM Sans Variable"', '"DM Sans"', 'system-ui', 'sans-serif'],
        serif: ['"Instrument Serif"', 'Georgia', 'serif'],
      },
      // Skala tipografi tunggal (9 langkah). Pakai HANYA token ini, bukan text-[NNpx].
      // Serif (font-serif / gm-display) hanya untuk display-xl, display, headline (>= 32px);
      // level di bawahnya memakai DM Sans dengan bobot 500 supaya hierarki tidak hanya dari ukuran.
      // Satuan rem: ikut pengaturan ukuran huruf browser pengguna (WCAG 1.4.4).
      fontSize: {
        'display-xl': ['clamp(3.5rem, 6.4vw, 7rem)', { lineHeight: '1', letterSpacing: '-0.025em' }], // 56–112px, hero
        display: ['clamp(2.75rem, 4.6vw, 4.5rem)', { lineHeight: '1.04', letterSpacing: '-0.02em' }], // 44–72px, judul halaman
        headline: ['clamp(2rem, 3.2vw, 3rem)', { lineHeight: '1.1', letterSpacing: '-0.015em' }], // 32–48px, judul section
        'title-lg': ['1.5rem', { lineHeight: '1.25', letterSpacing: '-0.01em', fontWeight: '500' }], // 24px, judul kartu
        title: ['1.25rem', { lineHeight: '1.35', letterSpacing: '-0.005em', fontWeight: '500' }], // 20px, sub-judul
        'body-lg': ['1.125rem', { lineHeight: '1.6' }], // 18px, lead
        body: ['1rem', { lineHeight: '1.6' }], // 16px, paragraf
        small: ['0.875rem', { lineHeight: '1.5' }], // 14px, nav, tombol, metadata
        label: ['0.75rem', { lineHeight: '1.4', letterSpacing: '0.01em', fontWeight: '500' }], // 12px, batas minimum
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
