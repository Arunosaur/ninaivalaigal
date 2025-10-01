import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@nina/ui': path.resolve(__dirname, '../../packages/ui/src'),
    },
  },
  server: {
    port: 8101,
    host: true,
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})
