import { render } from '@testing-library/react'
import { AxiosError, AxiosHeaders } from 'axios'
import { MemoryRouter } from 'react-router-dom'
import App from '../App'
import { AuthProvider } from '../contexts/AuthContext'
import type { SessionResponse, User } from '../types/auth'

export const ANA: User = {
  id: '6f1c2c1e-0000-4000-8000-000000000001',
  email: 'ana@example.com',
  display_name: 'Ana',
  created_at: '2026-11-09T19:00:00+00:00',
}

export function session(user: User = ANA, csrf = 'csrf-ana'): SessionResponse {
  return { user, csrf_token: csrf }
}

/** Cria um erro igual ao que o Axios lança quando a API responde com erro. */
export function apiError(status: number, error: { code: string; message: string; fields?: unknown }) {
  const headers = new AxiosHeaders()
  return new AxiosError('Request failed', 'ERR_BAD_RESPONSE', { headers }, null, {
    status,
    statusText: '',
    headers: {},
    config: { headers },
    data: { error },
  })
}

export const UNAUTHENTICATED = () =>
  apiError(401, { code: 'unauthenticated', message: 'Sua sessão expirou ou você não está conectado.' })

/** Renderiza a aplicação completa (rotas + autenticação) numa URL inicial. */
export function renderApp(path: string, state?: unknown) {
  return render(
    <MemoryRouter initialEntries={[state ? { pathname: path, state } : path]}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </MemoryRouter>,
  )
}
