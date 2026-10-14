import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
      '@contract': path.resolve(import.meta.dirname, '../contract'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      // 127.0.0.1, not localhost: on Windows "localhost" tries IPv6 ::1 first, and uvicorn listens on IPv4 only.
      '/api': 'http://127.0.0.1:8000',
    },
    // fixture mode imports JSON from ../contract
    fs: { allow: ['..'] },
  },
})
