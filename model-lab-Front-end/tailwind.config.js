/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        glowmatch: {
          primary: '#6B46C1', 
          secondary: '#1A202C', 
          background: '#FAFAFA'
        }
      },
      fontFamily: {
        sans: ['Poppins', 'Inter', 'sans-serif'],
      },
      // Tambahkan keyframes untuk animasi scanline
      keyframes: {
        scan: {
          '0%, 100%': { transform: 'translateY(0%)' },
          '50%': { transform: 'translateY(400px)' }, // 400px adalah estimasi tinggi oval
        }
      },
      animation: {
        'scan': 'scan 3s ease-in-out infinite',
      }
    },
  },
  plugins: [],
}