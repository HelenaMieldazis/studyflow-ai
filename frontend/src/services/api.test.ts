import type { InternalAxiosRequestConfig } from 'axios'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { api, setCsrfToken, setUnauthenticatedHandler } from './api'

let lastConfig: InternalAxiosRequestConfig | null = null
const originalAdapter = api.defaults.adapter

function respondWith(status: number, data: unknown) {
  api.defaults.adapter = async (config) => {
    lastConfig = config
    if (status >= 400) {
      const { AxiosError } = await import('axios')
      throw new AxiosError('fail', 'ERR_BAD_RESPONSE', config, null, {
        status,
        statusText: '',
        headers: {},
        config,
        data,
      })
    }
    return { status, statusText: '', headers: {}, config, data }
  }
}

beforeEach(() => {
  lastConfig = null
  setCsrfToken(null)
  setUnauthenticatedHandler(null)
})

afterEach(() => {
  api.defaults.adapter = originalAdapter
})

describe('cliente api', () => {
  it('envia o token CSRF em requisições que alteram dados', async () => {
    setCsrfToken('token-123')
    respondWith(200, {})

    for (const method of ['post', 'put', 'patch', 'delete'] as const) {
      await api.request({ url: '/x', method })
      expect(lastConfig?.headers.get('X-CSRF-Token')).toBe('token-123')
    }
  })

  it('não envia o token CSRF em GET', async () => {
    setCsrfToken('token-123')
    respondWith(200, {})

    await api.get('/x')
    expect(lastConfig?.headers.get('X-CSRF-Token')).toBeUndefined()
  })

  it('avisa o app quando a sessão expira (401 unauthenticated)', async () => {
    const handler = vi.fn()
    setUnauthenticatedHandler(handler)
    respondWith(401, { error: { code: 'unauthenticated', message: '...' } })

    await expect(api.get('/users/me')).rejects.toBeTruthy()
    expect(handler).toHaveBeenCalledOnce()
  })

  it('não trata "senha incorreta" (401 invalid_credentials) como sessão expirada', async () => {
    const handler = vi.fn()
    setUnauthenticatedHandler(handler)
    respondWith(401, { error: { code: 'invalid_credentials', message: '...' } })

    await expect(api.post('/auth/login', {})).rejects.toBeTruthy()
    expect(handler).not.toHaveBeenCalled()
  })

  it('nunca grava nada no localStorage nem no sessionStorage', async () => {
    setCsrfToken('token-123')
    respondWith(200, {})
    await api.post('/x')

    expect(window.localStorage.length).toBe(0)
    expect(window.sessionStorage.length).toBe(0)
  })
})
