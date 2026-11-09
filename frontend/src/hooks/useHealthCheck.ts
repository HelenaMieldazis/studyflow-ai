import axios from 'axios'
import { useCallback, useEffect, useState } from 'react'
import { fetchConnectionState } from '../services/healthService'
import type { ConnectionState } from '../types/health'

/** Carrega o estado de saúde da API e permite nova verificação manual. */
export function useHealthCheck() {
  // O estado inicial já é "loading"; o efeito só aplica o resultado da requisição.
  const [state, setState] = useState<ConnectionState>({ kind: 'loading' })
  // Incrementar este contador dispara uma nova verificação.
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    fetchConnectionState(controller.signal)
      .then((result) => {
        if (!controller.signal.aborted) setState(result)
      })
      .catch((error: unknown) => {
        if (!axios.isCancel(error)) setState({ kind: 'offline' })
      })
    // Cancela a requisição se o componente desmontar ou se houver nova tentativa.
    return () => controller.abort()
  }, [attempt])

  /** Acionado pelo usuário (evento), por isso pode marcar "loading" antes de buscar. */
  const retry = useCallback(() => {
    setState({ kind: 'loading' })
    setAttempt((n) => n + 1)
  }, [])

  return { state, retry }
}
