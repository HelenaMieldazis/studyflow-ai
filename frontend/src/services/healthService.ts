import axios from 'axios'
import { api } from './api'
import type { ConnectionState, HealthResponse } from '../types/health'

function isHealthResponse(value: unknown): value is HealthResponse {
  if (typeof value !== 'object' || value === null) return false
  const v = value as Record<string, unknown>
  const checks = v.checks as Record<string, unknown> | undefined
  return (
    (v.status === 'ok' || v.status === 'degraded') &&
    typeof v.service === 'string' &&
    typeof checks === 'object' &&
    checks !== null &&
    (checks.database === 'ok' || checks.database === 'unavailable')
  )
}

/**
 * Consulta /api/health e converte o resultado num estado de conexão.
 * O backend responde 503 quando o banco está fora; isso vira "degraded".
 * Respostas fora do formato esperado são tratadas como "offline".
 */
export async function fetchConnectionState(signal?: AbortSignal): Promise<ConnectionState> {
  try {
    const response = await api.get<unknown>('/health', {
      signal,
      // 503 é uma resposta válida deste endpoint, não um erro de rede.
      validateStatus: (status) => status === 200 || status === 503,
    })
    if (!isHealthResponse(response.data)) return { kind: 'offline' }
    return response.data.status === 'ok'
      ? { kind: 'online', data: response.data }
      : { kind: 'degraded', data: response.data }
  } catch (error) {
    if (axios.isCancel(error)) throw error
    return { kind: 'offline' }
  }
}
