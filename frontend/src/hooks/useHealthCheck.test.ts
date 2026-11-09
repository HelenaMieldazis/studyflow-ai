import { act, renderHook, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { fetchConnectionState } from '../services/healthService'
import { useHealthCheck } from './useHealthCheck'

vi.mock('../services/healthService', () => ({ fetchConnectionState: vi.fn() }))

describe('useHealthCheck', () => {
  it('começa em loading, carrega o estado e permite nova verificação', async () => {
    const mocked = vi.mocked(fetchConnectionState)
    mocked.mockResolvedValueOnce({ kind: 'offline' })

    const { result } = renderHook(() => useHealthCheck())
    expect(result.current.state).toEqual({ kind: 'loading' })
    await waitFor(() => expect(result.current.state).toEqual({ kind: 'offline' }))

    const data = { status: 'ok', service: 'studyflow-api', checks: { database: 'ok' } } as const
    mocked.mockResolvedValueOnce({ kind: 'online', data })
    act(() => result.current.retry())
    await waitFor(() => expect(result.current.state).toEqual({ kind: 'online', data }))
    expect(mocked).toHaveBeenCalledTimes(2)
  })
})
