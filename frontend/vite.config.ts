/// <reference types="vitest/config" />
import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

// O .env fica na raiz do repositório (compartilhado com o backend e o Docker Compose).
// Apenas variáveis com prefixo VITE_ são expostas ao código do navegador.
const ENV_DIR = '..'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ENV_DIR, 'VITE_')
  const proxyTarget = env.VITE_DEV_PROXY_TARGET || 'http://127.0.0.1:5001'

  return {
    envDir: ENV_DIR,
    plugins: [react()],
    server: {
      port: 5173,
      strictPort: true,
      // Em desenvolvimento, /api é encaminhado ao Flask: o navegador vê uma única
      // origem, o que simplifica cookies HttpOnly e CSRF na Etapa 2.
      proxy: {
        '/api': {
          target: proxyTarget,
          changeOrigin: false,
        },
      },
    },
    build: {
      sourcemap: false,
    },
    test: {
      environment: 'jsdom',
      globals: false,
      setupFiles: ['./src/test/setup.ts'],
      css: { modules: { classNameStrategy: 'non-scoped' } },
      restoreMocks: true,
    },
  }
})
