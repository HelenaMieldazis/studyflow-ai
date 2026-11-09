import axios from 'axios'

/**
 * Cliente HTTP único da aplicação.
 *
 * - Todas as chamadas ao backend passam por aqui (nunca use fetch/axios direto nas telas).
 * - `withCredentials` permite enviar cookies HttpOnly de sessão (Etapa 2).
 * - Nenhum token é guardado em localStorage.
 */
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10_000,
  withCredentials: true,
  headers: { Accept: 'application/json' },
})
