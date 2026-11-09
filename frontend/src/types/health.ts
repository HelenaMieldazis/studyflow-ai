/** Resposta de GET /api/health (espelha app/routes/health.py). */
export type HealthResponse = {
  status: 'ok' | 'degraded'
  service: string
  checks: {
    database: 'ok' | 'unavailable'
  }
}

/** Estado de conexão exibido na interface. */
export type ConnectionState =
  | { kind: 'loading' }
  | { kind: 'online'; data: HealthResponse }
  | { kind: 'degraded'; data: HealthResponse }
  | { kind: 'offline' }
