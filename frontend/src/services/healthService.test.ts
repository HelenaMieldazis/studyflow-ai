import { AxiosError, AxiosHeaders, type AxiosResponse } from 'axios'
import { describe, expect, it, vi } from 'vitest'
import { api } from './api'
import { fetchConnectionState } from './healthService'

function mockResponse(data: unknown, status = 200): AxiosResponse {
  return { data, status, statusText: '', headers: {}, config: { headers: new AxiosHeaders() } }
}

describe('fetchConnectionState', () => {
  it('retorna "online" quando a API e o banco estão OK', async () => {
    const data = { status: 'ok', service: 'studyflow-api', checks: { database: 'ok' } }
    const spy = vi.spyOn(api, 'get').mockResolvedValue(mockResponse(data))

    await expect(fetchConnectionState()).resolves.toEqual({ kind: 'online', data })
    expect(spy).toHaveBeenCalledWith('/health', expect.any(Object))
  })

  it('retorna "degraded" quando a API responde 503 com banco indisponível', async () => {
    const data = { status: 'degraded', service: 'studyflow-api', checks: { database: 'unavailable' } }
    vi.spyOn(api, 'get').mockResolvedValue(mockResponse(data, 503))

    await expect(fetchConnectionState()).resolves.toEqual({ kind: 'degraded', data })
  })

  it('retorna "offline" em erro de rede', async () => {
    vi.spyOn(api, 'get').mockRejectedValue(new AxiosError('Network Error', 'ERR_NETWORK'))

    await expect(fetchConnectionState()).resolves.toEqual({ kind: 'offline' })
  })

  it('retorna "offline" quando a resposta não segue o formato esperado', async () => {
    vi.spyOn(api, 'get').mockResolvedValue(mockResponse('<html>proxy error</html>'))

    await expect(fetchConnectionState()).resolves.toEqual({ kind: 'offline' })
  })

  it('aceita apenas 200 e 503 como respostas válidas', async () => {
    const spy = vi
      .spyOn(api, 'get')
      .mockResolvedValue(mockResponse({ status: 'ok', service: 's', checks: { database: 'ok' } }))
    await fetchConnectionState()

    const options = spy.mock.calls[0][1] as { validateStatus: (s: number) => boolean }
    expect([200, 503, 500, 404].map(options.validateStatus)).toEqual([true, true, false, false])
  })
})

describe('cliente api', () => {
  it('usa /api como base, envia cookies e tem timeout', () => {
    expect(api.defaults.baseURL).toBe('/api')
    expect(api.defaults.withCredentials).toBe(true)
    expect(api.defaults.timeout).toBeGreaterThan(0)
  })
})
