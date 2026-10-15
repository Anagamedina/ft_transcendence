import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const rootDir = resolve(fileURLToPath(new URL('.', import.meta.url)), '..')

export default defineConfig(({ command }) => ({
  plugins: [vue()],
  server: command === 'serve' ? {
    host: 'localhost',
    port: 5173,
    strictPort: true,
    // `make dev` creates this pair. HTTPS keeps the Secure session cookie
    // usable when the browser talks to the Vite development server.
    https: {
      cert: readFileSync(resolve(rootDir, 'gateway/certs/aquaguard.crt')),
      key: readFileSync(resolve(rootDir, 'gateway/certs/aquaguard.key')),
    },
    proxy: {
      '/api/': {
        // Backend remains private inside Compose; development traffic follows
        // the same gateway path as production.
        target: 'https://localhost',
        changeOrigin: true,
        secure: false,
      },
    },
  } : undefined,
}))
