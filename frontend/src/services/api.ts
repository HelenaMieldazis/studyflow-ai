import axios, { AxiosError } from 'axios'

/**
 * Cliente HTTP único da aplicação.
 *
 * - Todas as chamadas ao backend passam por aqui (nunca use fetch/axios direto nas telas).
 * - A sessão fica num cookie HttpOnly que o JavaScript NÃO consegue ler; `withCredentials`
 *   faz o navegador enviá-lo.
 * - O token CSRF fica apenas em memória (nunca em localStorage) e é enviado no header
 *   X-CSRF-Token em toda requisição que altera dados.
 */
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10_000,
  withCredentials: true,
  headers: { Accept: 'application/json' },
})

const UNSAFE_METHODS = new Set(['post', 'put', 'patch', 'delete'])

let csrfToken: string | null = null
let onUnauthenticated: (() => void) | null = null

export function setCsrfToken(token: string | null) {
  csrfToken = token
}

/** Registrado pelo AuthProvider: chamado quando a sessão expira no meio do uso. */
export function setUnauthenticatedHandler(handler: (() => void) | null) {
  onUnauthenticated = handler
}

api.interceptors.request.use((config) => {
  if (csrfToken && config.method && UNSAFE_METHODS.has(config.method.toLowerCase())) {
    config.headers.set('X-CSRF-Token', csrfToken)
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    // Só reage à sessão expirada/inexistente — não a "senha incorreta" (que também é 401).
    if (
      error instanceof AxiosError &&
      error.response?.status === 401 &&
      (error.response.data as { error?: { code?: string } } | undefined)?.error?.code === 'unauthenticated'
    ) {
      csrfToken = null
      onUnauthenticated?.()
    }
    return Promise.reject(error)
  },
)
