import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { setCsrfToken, setUnauthenticatedHandler } from '../services/api'
import * as authService from '../services/authService'
import type { LoginInput, RegisterInput, SessionResponse, User } from '../types/auth'
import { AuthContext, type AuthContextValue, type AuthNotice, type AuthStatus } from './authContextValue'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>('loading')
  const [user, setUserState] = useState<User | null>(null)
  const [notice, setNotice] = useState<AuthNotice | null>(null)

  const applySession = useCallback((session: SessionResponse) => {
    setCsrfToken(session.csrf_token)
    setUserState(session.user)
    setStatus('authenticated')
    setNotice(null)
  }, [])

  const clearSession = useCallback((reason?: AuthNotice) => {
    setNotice(reason ?? null)
    setCsrfToken(null)
    setUserState(null)
    setStatus('anonymous')
  }, [])

  // Ao abrir/recarregar a página, descobre se ainda existe uma sessão válida no cookie.
  useEffect(() => {
    let active = true
    authService
      .fetchCurrentSession()
      .then((session) => {
        if (active) applySession(session)
      })
      .catch(() => {
        if (active) clearSession(undefined)
      })
    return () => {
      active = false
    }
  }, [applySession, clearSession])

  // Se qualquer chamada receber 401 "unauthenticated" durante o uso, a sessão acabou.
  useEffect(() => {
    setUnauthenticatedHandler(() => clearSession('session_expired'))
    return () => setUnauthenticatedHandler(null)
  }, [clearSession])

  const login = useCallback(
    async (input: LoginInput) => applySession(await authService.login(input)),
    [applySession],
  )

  const register = useCallback(
    async (input: RegisterInput) => applySession(await authService.register(input)),
    [applySession],
  )

  const logout = useCallback(async () => {
    try {
      await authService.logout()
    } finally {
      // Mesmo se a rede falhar, o estado local é limpo.
      clearSession('logged_out')
    }
  }, [clearSession])

  const value = useMemo<AuthContextValue>(
    () => ({
      status,
      user,
      notice,
      login,
      register,
      logout,
      setUser: setUserState,
      applySession,
      clearSession,
    }),
    [status, user, notice, login, register, logout, applySession, clearSession],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
