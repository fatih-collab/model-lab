import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [react()],
  server: {
    // Backend FastAPI (Fase 2). Kamera (getUserMedia) hanya jalan di localhost atau HTTPS.
    proxy: {
      '/api': loadEnv(mode, '.', '').VITE_PROXY_TARGET || 'http://localhost:8000',
    },
  },
}))
