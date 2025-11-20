import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg}']
      },
      includeAssets: ['family-icon.svg', 'family-icon-192.png', 'family-icon-512.png'],
      manifest: {
        name: 'Family Assistant',
        short_name: 'Family',
        description: 'Your family\'s AI assistant for homework help, scheduling, and coordination',
        theme_color: '#8b6f47',
        background_color: '#fef7f0',
        display: 'standalone',
        icons: [
          {
            src: 'family-icon-192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'family-icon-512.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ],
        categories: ['lifestyle', 'education', 'productivity'],
        lang: 'en',
        dir: 'ltr',
        orientation: 'portrait-primary',
        start_url: '/',
        scope: '/'
      }
    })
  ],
  server: {
    port: 3000,
    host: true,
    cors: true
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          router: ['react-router-dom'],
          query: ['@tanstack/react-query'],
          icons: ['lucide-react']
        }
      }
    }
  }
})