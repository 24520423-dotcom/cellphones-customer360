import { cwd } from 'node:process'
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig(({ mode }) => {
  const { FRAPPE_PROXY_TARGET } = loadEnv(mode, cwd(), 'FRAPPE_')

  return {
    plugins: [react(), tailwindcss()],
    server: FRAPPE_PROXY_TARGET ? {
      proxy: {
        '/api': {
          target: FRAPPE_PROXY_TARGET,
          changeOrigin: true,
          cookieDomainRewrite: '',
        },
      },
    } : undefined,
  }
})
